from __future__ import annotations
import re
from dataclasses import dataclass

@dataclass
class EntityMatch:
    kind: str
    value: str
    object_id: int | None = None
    label: str | None = None
    confidence: str = "medium"
    reason: str = ""

def norm(s):
    return re.sub(r"[^a-z0-9]+"," ",(s or "").lower()).strip()

def _person_matches(db,text,limit=10):
    qn=norm(text)
    qt=set(qn.split())
    rows=[]
    for p in db.execute("SELECT id,display_name,gedcom_xref FROM people"):
        name=norm(p["display_name"])
        toks=set(name.split())
        if not toks:
            continue
        exact=name in qn
        overlap=len(toks & qt)
        if exact:
            score=1000+len(toks)
        elif overlap >= min(2,len(toks)):
            score=overlap*20 + overlap/max(1,len(toks))
        else:
            continue
        rows.append((score,p))
    rows.sort(key=lambda x:(-x[0],x[1]["display_name"]))
    return [r for _,r in rows[:limit]]

def resolve_entities(db,text,limit=12):
    """
    Resolve obvious entities before deciding how to search them.
    This is deterministic and evidence-based: people come from the people table,
    sources from source records, identifiers/topics from indexed content.
    """
    raw=text.strip()
    n=norm(raw)
    out=[]

    # Direct IDs/xrefs.
    m=re.search(r"(?<!\w)@I(\d+)@(?!\w)",raw,re.I)
    if m:
        r=db.execute("SELECT id,display_name FROM people WHERE gedcom_xref=?",(f"@I{m.group(1)}@",)).fetchone()
        if r: out.append(EntityMatch("person",raw,r["id"],r["display_name"],"high","GEDCOM person xref"))
    if raw.isdigit():
        r=db.execute("SELECT id,display_name FROM people WHERE id=?",(int(raw),)).fetchone()
        if r: out.append(EntityMatch("person",raw,r["id"],r["display_name"],"high","Companion person ID"))

    # Person names embedded in a sentence.
    for r in _person_matches(db,raw,limit=limit):
        conf="high" if norm(r["display_name"]) in n else "medium"
        out.append(EntityMatch("person",r["display_name"],r["id"],r["display_name"],conf,
                               "person name found in imported Reunion data"))

    # Source xref.
    m=re.search(r"(?<!\w)@?S(\d+)@?(?!\w)",raw,re.I)
    if m:
        x=f"@S{m.group(1)}@"
        s=db.execute("SELECT id,gedcom_xref,display_text,text,title FROM sources WHERE gedcom_xref=?",(x,)).fetchone()
        if s:
            out.append(EntityMatch("source",x,s["id"],s["display_text"] or s["text"] or s["title"] or x,
                                   "high","GEDCOM source xref"))

    # Common service/record identifiers: letters+digits or long numeric refs.
    for token in re.findall(r"\b[A-Z]{1,5}\d{3,}\b|\b\d{3,}[-/]\d+\b",raw.upper()):
        out.append(EntityMatch("identifier",token,None,token,"medium","identifier-like token"))

    # If no structural entity dominates, preserve a topic phrase.
    if not out:
        phrase=re.sub(r"\b(what|which|who|where|when|why|how|records?|mentions?|mention|show|find|tell|me|about|do|does|did|is|are|was|were)\b"," ",raw,flags=re.I)
        phrase=" ".join(phrase.split()).strip(" ?.,")
        if phrase:
            out.append(EntityMatch("topic",phrase,None,phrase,"low","remaining subject phrase"))
    return out[:limit]

def format_resolve(db,text):
    matches=resolve_entities(db,text)
    L=[f"Entity Resolution — {text}","="*(20+len(text))]
    if not matches:
        return "\n".join(L+["  (no entity resolved)"])
    for m in matches:
        ident=f" [ID {m.object_id}]" if m.object_id is not None else ""
        L.append(f"  {m.kind:<10} {m.label or m.value}{ident} — {m.confidence} — {m.reason}")
    return "\n".join(L)
