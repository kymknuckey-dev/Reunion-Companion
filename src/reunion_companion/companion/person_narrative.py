from __future__ import annotations
import hashlib, json
from .local_llm import OllamaClient, LocalLLMError

NARRATIVE_VERSION = "ffd-1.9-build-2-v1"

def _ensure_cache(db):
    db.execute("""CREATE TABLE IF NOT EXISTS companion_person_narrative_cache(
      person_id INTEGER PRIMARY KEY, source_hash TEXT NOT NULL, narrative_version TEXT NOT NULL,
      narrative TEXT NOT NULL, generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")

def _evidence(db,pid):
    p=db.execute("SELECT id,display_name,sex FROM people WHERE id=?",(pid,)).fetchone()
    if not p:return None,[],[]
    notes=[r[0] for r in db.execute("SELECT text FROM notes WHERE person_id=? ORDER BY id",(pid,)) if (r[0] or '').strip()]
    facts=[]
    for r in db.execute("SELECT event_type,date_text,place_text,value_text,note_text FROM events WHERE person_id=? ORDER BY id",(pid,)):
        vals=[r[0] or 'Fact']+[x for x in r[1:] if x]
        facts.append(" — ".join(str(x) for x in vals))
    return dict(p),notes,facts

def source_fingerprint(db,pid):
    p,notes,facts=_evidence(db,pid)
    raw=json.dumps({"person":p,"notes":notes,"facts":facts},ensure_ascii=False,sort_keys=True)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def person_narrative(db,pid,client=None,force=False):
    p,notes,facts=_evidence(db,pid)
    if not p:return {"status":"missing","narrative":"","cached":False}
    _ensure_cache(db); fp=source_fingerprint(db,pid)
    if not force:
        row=db.execute("SELECT narrative FROM companion_person_narrative_cache WHERE person_id=? AND source_hash=? AND narrative_version=?",(pid,fp,NARRATIVE_VERSION)).fetchone()
        if row:return {"status":"ok","narrative":row[0],"cached":True}
    evidence="\n\n".join(x.replace('\r\n','\n').replace('\r','\n').strip() for x in notes if x.strip())
    fact_text="\n".join(f"- {x}" for x in facts)
    if not evidence and not fact_text:
        return {"status":"empty","narrative":"No biographical material is recorded for this person.","cached":False}
    prompt=f'''Write a concise, readable family-history biography of {p['display_name']} for Presentation mode.\n\nSTRICT GROUNDING RULES:\n- Use ONLY the ORIGINAL REUNION NOTES and STRUCTURED REUNION FACTS supplied below.\n- Do not infer or invent dates, places, relationships, motives, occupations, achievements, health details or other facts.\n- Preserve names, dates and factual claims accurately.\n- Organise the material into natural chronological or thematic paragraphs.\n- Remove obvious repetition and improve grammar and flow.\n- Do not mention databases, GEDCOM, Reunion, evidence bundles, or these instructions.\n- Return biography prose only, with paragraphs separated by blank lines.\n\nSTRUCTURED REUNION FACTS:\n{fact_text or '(none)'}\n\nORIGINAL REUNION NOTES:\n{evidence or '(none)'}\n'''
    try:
        narrative=(client or OllamaClient()).generate(prompt).strip()
        status="ok"
    except LocalLLMError as exc:
        narrative=evidence or "\n".join(facts)
        status="fallback"
    db.execute("INSERT INTO companion_person_narrative_cache(person_id,source_hash,narrative_version,narrative) VALUES(?,?,?,?) ON CONFLICT(person_id) DO UPDATE SET source_hash=excluded.source_hash,narrative_version=excluded.narrative_version,narrative=excluded.narrative,generated_at=CURRENT_TIMESTAMP",(pid,fp,NARRATIVE_VERSION,narrative));db.commit()
    return {"status":status,"narrative":narrative,"cached":False}

def invalidate_person_narrative(db,pid=None):
    _ensure_cache(db)
    if pid is None: db.execute("DELETE FROM companion_person_narrative_cache")
    else: db.execute("DELETE FROM companion_person_narrative_cache WHERE person_id=?",(pid,))
    db.commit()
