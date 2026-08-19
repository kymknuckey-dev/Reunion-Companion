from __future__ import annotations
import hashlib, json
from .local_llm import OllamaClient, LocalLLMError

NARRATIVE_VERSION = "ffd-1.9-build-4.0.1-v1"

def _ensure_cache(db):
    db.execute("""CREATE TABLE IF NOT EXISTS companion_person_narrative_cache(
      person_id INTEGER PRIMARY KEY, source_hash TEXT NOT NULL, narrative_version TEXT NOT NULL,
      narrative TEXT NOT NULL, generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")

def _family_units(db,pid):
    """Authoritative spouse-family units for this person; never infer kinship."""
    rows=db.execute("""SELECT DISTINCT f.id,f.marriage_date,f.marriage_place
      FROM families f JOIN family_members mine ON mine.family_id=f.id
      WHERE mine.person_id=? AND lower(mine.role) IN ('husband','wife','spouse')
      ORDER BY f.id""",(pid,)).fetchall()
    out=[]
    for f in rows:
        spouses=[dict(r) for r in db.execute("""SELECT p.id,p.display_name FROM family_members fm
          JOIN people p ON p.id=fm.person_id WHERE fm.family_id=? AND fm.person_id<>?
          AND lower(fm.role) IN ('husband','wife','spouse') ORDER BY p.id""",(f["id"],pid))]
        children=[dict(r) for r in db.execute("""SELECT p.id,p.display_name FROM family_members fm
          JOIN people p ON p.id=fm.person_id WHERE fm.family_id=? AND lower(fm.role)='child'
          ORDER BY p.id""",(f["id"],))]
        out.append({"family_id":f["id"],"marriage_date":f["marriage_date"] or "",
                    "marriage_place":f["marriage_place"] or "","spouses":spouses,"children":children})
    return out

def _evidence(db,pid):
    p=db.execute("SELECT id,display_name,sex FROM people WHERE id=?",(pid,)).fetchone()
    if not p:return None,[],[],[]
    notes=[r[0] for r in db.execute("SELECT text FROM notes WHERE person_id=? ORDER BY id",(pid,)) if (r[0] or '').strip()]
    facts=[]
    for r in db.execute("SELECT event_type,date_text,place_text,value_text,note_text,gedcom_tag FROM events WHERE person_id=? ORDER BY id",(pid,)):
        typ=(r[0] or 'Fact').strip()
        # Reunion/GEDCOM CHAN/Changed metadata describes database editing, not a life event.
        if typ.casefold() in ('changed','change') or (r[5] or '').upper()=='CHAN':
            continue
        vals=[typ]+[x for x in r[1:5] if x]
        facts.append(" — ".join(str(x) for x in vals))
    return dict(p),notes,facts,_family_units(db,pid)

def source_fingerprint(db,pid):
    p,notes,facts,families=_evidence(db,pid)
    raw=json.dumps({"person":p,"notes":notes,"facts":facts,"families":families},ensure_ascii=False,sort_keys=True)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def _family_text(families):
    lines=[]
    for f in families:
        spouses=", ".join(x["display_name"] for x in f["spouses"]) or "(none)"
        children=", ".join(x["display_name"] for x in f["children"]) or "(none)"
        lines.append(f"Family {f['family_id']}: spouse(s): {spouses}; marriage date: {f['marriage_date'] or '(not recorded)'}; marriage place: {f['marriage_place'] or '(not recorded)'}; children of this family: {children}.")
    return "\n".join(lines)

def _join_names(names):
    if not names:return ""
    if len(names)==1:return names[0]
    if len(names)==2:return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1])+", and "+names[-1]

def _deterministic_family_sentence(person,fam,include_spouse=True,include_children=True):
    spouse_names=[x["display_name"] for x in fam["spouses"]]
    child_names=[x["display_name"] for x in fam["children"]]
    parts=[]
    if include_spouse and spouse_names:
        spouse=_join_names(spouse_names)
        marriage=f"{person['display_name']} married {spouse}"
        if fam["marriage_date"]: marriage+=f" on {fam['marriage_date']}"
        if fam["marriage_place"]: marriage+=f" at {fam['marriage_place'].rstrip('.')}"
        parts.append(marriage+".")
    if include_children and child_names:
        lead="They" if include_spouse and spouse_names else person["display_name"]
        n=len(child_names); word="child" if n==1 else "children"
        parts.append(f"{lead} had {n} {word}: {_join_names(child_names)}.")
    return " ".join(parts)

def _family_children_covered_together(narrative,fam):
    """A family is covered only when all recorded children occur in one family passage.

    A child's name elsewhere in unrelated prose (for example as a property owner)
    must not satisfy immediate-family completeness.
    """
    children=[x["display_name"] for x in fam["children"]]
    if not children:
        return True
    paras=[p.strip() for p in (narrative or "").split("\n\n") if p.strip()]
    for para in paras:
        low=para.casefold()
        if all(name.casefold() in low for name in children):
            # Require explicit child-family language in the same passage.
            if "child" in low or "children" in low or "son" in low or "daughter" in low:
                return True
    return False

def _ensure_family_grounding(narrative,person,families):
    """Guarantee complete recorded spouse-family units without inferring kinship."""
    paragraphs=[x.strip() for x in (narrative or "").split("\n\n") if x.strip()]
    for fam in families:
        text="\n\n".join(paragraphs)
        spouse_names=[x["display_name"] for x in fam["spouses"]]
        child_names=[x["display_name"] for x in fam["children"]]
        spouse_present=all(n.casefold() in text.casefold() for n in spouse_names)
        children_covered=_family_children_covered_together(text,fam)

        if spouse_present and children_covered:
            continue

        # If an existing paragraph already contains the spouse, preserve it and
        # add the COMPLETE recorded child set beside that context. Never compute
        # a partial child list from names found elsewhere in the biography.
        idx=next((i for i,p in enumerate(paragraphs)
                  if spouse_names and all(n.casefold() in p.casefold() for n in spouse_names)),None)

        if idx is not None and spouse_present:
            if child_names and not children_covered:
                n=len(child_names); word="child" if n==1 else "children"
                sentence=f"They had {n} {word}: {_join_names(child_names)}."
                paragraphs[idx]=paragraphs[idx].rstrip()+" "+sentence
        else:
            sentence=_deterministic_family_sentence(person,fam,True,True)
            insert_at=1 if paragraphs else 0
            paragraphs.insert(insert_at,sentence)

    return "\n\n".join(paragraphs)

def _deterministic_fact_narrative(person,facts,families):
    """Safe publication prose for people whose biography is facts-only.

    Facts are rendered without verbs that imply a change, cause or chronology not
    present in Reunion. This deliberately prefers plain evidence over fluent invention.
    """
    paras=[]
    if facts:
        paras.append(person["display_name"]+" has the following recorded life facts: " + "; ".join(facts)+".")
    for fam in families:
        sentence=_deterministic_family_sentence(person,fam,True,True)
        if sentence: paras.append(sentence)
    return "\n\n".join(paras)

def person_narrative(db,pid,client=None,force=False):
    p,notes,facts,families=_evidence(db,pid)
    if not p:return {"status":"missing","narrative":"","cached":False}
    _ensure_cache(db); fp=source_fingerprint(db,pid)
    if not force:
        # RC1: the stored Biography is canonical until explicit regeneration.
        row=db.execute("SELECT narrative FROM companion_person_narrative_cache WHERE person_id=?",(pid,)).fetchone()
        if row:return {"status":"ok","narrative":row[0],"cached":True}
    evidence="\n\n".join(x.replace('\r\n','\n').replace('\r','\n').strip() for x in notes if x.strip())
    fact_text="\n".join(f"- {x}" for x in facts)
    family_text=_family_text(families)
    if not evidence and not fact_text:
        return {"status":"empty","narrative":"No biographical material is recorded for this person.","cached":False}
    # Facts-only biographies are deterministic.  Without authored Reunion notes,
    # an LLM has no narrative context from which to infer verbs such as 'changed'.
    if not evidence and fact_text:
        narrative=_deterministic_fact_narrative(p,facts,families)
        db.execute("INSERT INTO companion_person_narrative_cache(person_id,source_hash,narrative_version,narrative) VALUES(?,?,?,?) ON CONFLICT(person_id) DO UPDATE SET source_hash=excluded.source_hash,narrative_version=excluded.narrative_version,narrative=excluded.narrative,generated_at=CURRENT_TIMESTAMP",(pid,fp,NARRATIVE_VERSION,narrative));db.commit()
        return {"status":"ok","narrative":narrative,"cached":False}
    prompt=f'''Write a concise, readable family-history biography of {p['display_name']} for Presentation mode.\n\nSTRICT GROUNDING RULES:\n- Use ONLY the ORIGINAL REUNION NOTES and STRUCTURED REUNION FACTS supplied below.\n- Do not infer or invent dates, places, relationships, motives, occupations, achievements, health details or other facts.\n- Preserve names, dates and factual claims accurately.\n- Organise the material into natural chronological or thematic paragraphs.\n- Introduce the subject by full name, then use the subject's given/first name naturally in later references and possessives.\n- Do not refer to the subject as Mr, Mrs, Ms, Miss or another courtesy title unless that title is itself part of the recorded evidence and historically significant.\n- Remove obvious repetition and improve grammar and flow.\n- Do not mention databases, GEDCOM, Reunion, evidence bundles, or these instructions.\n- Treat IMMEDIATE FAMILY FACTS as authoritative: incorporate the recorded spouse, marriage details and every child naturally in the biography. Never change a child's relationship or invent a family member.\n- Return biography prose only, with paragraphs separated by blank lines. Do not add a title or Markdown heading.\n\nIMMEDIATE FAMILY FACTS (authoritative):\n{family_text or '(none recorded)'}\n\nSTRUCTURED REUNION FACTS:\n{fact_text or '(none)'}\n\nORIGINAL REUNION NOTES:\n{evidence or '(none)'}\n'''
    try:
        narrative=(client or OllamaClient()).generate(prompt).strip()
        narrative=_ensure_family_grounding(narrative,p,families)
        status="ok"
    except LocalLLMError as exc:
        narrative=_ensure_family_grounding(evidence or "\n".join(facts),p,families)
        status="fallback"
    db.execute("INSERT INTO companion_person_narrative_cache(person_id,source_hash,narrative_version,narrative) VALUES(?,?,?,?) ON CONFLICT(person_id) DO UPDATE SET source_hash=excluded.source_hash,narrative_version=excluded.narrative_version,narrative=excluded.narrative,generated_at=CURRENT_TIMESTAMP",(pid,fp,NARRATIVE_VERSION,narrative));db.commit()
    return {"status":status,"narrative":narrative,"cached":False}

def cached_person_narrative(db,pid):
    """Return the canonical stored Biography without generating it."""
    _ensure_cache(db)
    row=db.execute("SELECT narrative,generated_at FROM companion_person_narrative_cache WHERE person_id=?",(pid,)).fetchone()
    return {"narrative":row[0],"generated_at":row[1]} if row else None

def invalidate_person_narrative(db,pid=None):
    _ensure_cache(db)
    if pid is None: db.execute("DELETE FROM companion_person_narrative_cache")
    else: db.execute("DELETE FROM companion_person_narrative_cache WHERE person_id=?",(pid,))
    db.commit()
