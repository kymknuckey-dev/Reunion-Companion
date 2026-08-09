from __future__ import annotations
from collections import deque, defaultdict
from dataclasses import dataclass

@dataclass(frozen=True)
class PersonEdge:
    left: int
    right: int
    relation: str
    family_id: int | None = None


def _name(db,pid):
    r=db.execute("SELECT display_name FROM people WHERE id=?",(pid,)).fetchone()
    return r["display_name"] if r else f"Person {pid}"


def person_edges(db):
    """Return deterministic person-to-person edges derived from GEDCOM families.

    Only genealogically meaningful structural edges are created here: spouse and
    parent/child. Sibling relationships remain derivable through shared parents,
    which avoids inventing an extra edge that could distort shortest paths.
    """
    edges=[]
    for f in db.execute("SELECT id FROM families ORDER BY id"):
        members=db.execute("SELECT person_id,role FROM family_members WHERE family_id=? ORDER BY person_id",(f["id"],)).fetchall()
        spouses=[m["person_id"] for m in members if m["role"] in ("HUSB","WIFE","SPOU","Husband","Wife","Spouse")]
        children=[m["person_id"] for m in members if m["role"] in ("CHIL","Child")]
        for i,a in enumerate(spouses):
            for b in spouses[i+1:]:
                edges.append(PersonEdge(a,b,"spouse",f["id"]))
                edges.append(PersonEdge(b,a,"spouse",f["id"]))
        for parent in spouses:
            for child in children:
                edges.append(PersonEdge(parent,child,"parent",f["id"]))
                edges.append(PersonEdge(child,parent,"child",f["id"]))
        for i,a in enumerate(children):
            for b in children[i+1:]:
                edges.append(PersonEdge(a,b,"sibling",f["id"]))
                edges.append(PersonEdge(b,a,"sibling",f["id"]))
    return edges


def adjacency(db):
    adj=defaultdict(list)
    for e in person_edges(db):
        adj[e.left].append(e)
    for pid in adj:
        adj[pid].sort(key=lambda e:(_name(db,e.right),e.relation,e.family_id or 0))
    return adj


def relationship_path(db,start_id,end_id,max_depth=12):
    """Shortest structural relationship path between two people."""
    if start_id==end_id:return []
    adj=adjacency(db); q=deque([(start_id,[])]) ; seen={start_id}
    while q:
        node,path=q.popleft()
        if len(path)>=max_depth: continue
        for e in adj.get(node,[]):
            if e.right in seen: continue
            np=path+[e]
            if e.right==end_id:return np
            seen.add(e.right); q.append((e.right,np))
    return None


def format_path(db,start_id,end_id,max_depth=12):
    a=_name(db,start_id); b=_name(db,end_id)
    title=f"Relationship Path — {a} → {b}"; L=[title,"="*len(title)]
    p=relationship_path(db,start_id,end_id,max_depth)
    if p is None:
        return "\n".join(L+[f"  No structural family path found within {max_depth} steps."])
    if not p:
        return "\n".join(L+["  Same person."])
    current=start_id
    L.append(f"  {_name(db,current)} [ID {current}]")
    for e in p:
        arrow={"parent":"is parent of","child":"is child of","spouse":"is spouse of","sibling":"is sibling of"}.get(e.relation,e.relation)
        L.append(f"    └─ {arrow} → {_name(db,e.right)} [ID {e.right}] (Family {e.family_id})")
        current=e.right
    L += ["",f"Steps: {len(p)}"]
    return "\n".join(L)


def neighbourhood(db,pid,depth=2,limit=100):
    adj=adjacency(db); q=deque([(pid,0)]); seen={pid}; rows=[]
    while q and len(rows)<limit:
        node,d=q.popleft()
        if d>=depth:continue
        for e in adj.get(node,[]):
            if e.right in seen:continue
            seen.add(e.right);rows.append((d+1,e))
            q.append((e.right,d+1))
    return rows


def format_neighbourhood(db,pid,depth=2):
    name=_name(db,pid);title=f"Relationship Graph — {name} — depth {depth}";L=[title,"="*len(title)]
    rows=neighbourhood(db,pid,depth)
    if not rows:return "\n".join(L+["  (no connected people)"])
    for d,e in rows:
        arrow={"parent":"parent of","child":"child of","spouse":"spouse of","sibling":"sibling of"}.get(e.relation,e.relation)
        L.append(f"  {'  '*(d-1)}G{d}: {_name(db,e.right)} [ID {e.right}] — via {arrow}")
    return "\n".join(L)


def evidence_graph(db,pid):
    """Build a semantic evidence graph around one person from the Companion model."""
    nodes=[];edges=[]
    def add(kind,oid,label):
        key=f"{kind}:{oid}";nodes.append({"key":key,"kind":kind,"id":oid,"label":label});return key
    pk=add("person",pid,_name(db,pid))
    families=db.execute("SELECT DISTINCT f.* FROM families f JOIN family_members fm ON fm.family_id=f.id WHERE fm.person_id=? ORDER BY f.id",(pid,)).fetchall()
    for f in families:
        label=f["gedcom_xref"] or f"Family {f['id']}";fk=add("family",f["id"],label);edges.append((pk,fk,"member of"))
    ev=db.execute("SELECT * FROM events WHERE person_id=? ORDER BY id",(pid,)).fetchall()
    for e in ev:
        label=e["event_type"]+(f" — {e['date_text']}" if e["date_text"] else "");ek=add("event",e["id"],label);edges.append((pk,ek,"has event"))
        for s in db.execute("SELECT s.* FROM sources s JOIN event_sources es ON es.source_id=s.id WHERE es.event_id=?",(e["id"],)):
            sk=add("source",s["id"],s["display_text"] or s["text"] or s["title"] or s["gedcom_xref"]);edges.append((ek,sk,"cited by"))
        for m in db.execute("SELECT m.* FROM media m JOIN event_media em ON em.media_id=m.id WHERE em.event_id=?",(e["id"],)):
            mk=add("media",m["id"],m["title"] or m["file_path"]);edges.append((ek,mk,"documented by"))
    for n in db.execute("SELECT * FROM notes WHERE person_id=? ORDER BY id",(pid,)):
        nk=add("note",n["id"],n["note_type"] or n["gedcom_tag"] or "Note");edges.append((pk,nk,"has note"))
        for s in db.execute("SELECT s.* FROM sources s JOIN note_sources ns ON ns.source_id=s.id WHERE ns.note_id=?",(n["id"],)):
            sk=add("source",s["id"],s["display_text"] or s["text"] or s["title"] or s["gedcom_xref"]);edges.append((nk,sk,"cited by"))
    for m in db.execute("SELECT m.* FROM media m JOIN person_media pm ON pm.media_id=m.id WHERE pm.person_id=?",(pid,)):
        mk=add("media",m["id"],m["title"] or m["file_path"]);edges.append((pk,mk,"has media"))
    for s in db.execute("SELECT s.* FROM sources s JOIN person_sources ps ON ps.source_id=s.id WHERE ps.person_id=?",(pid,)):
        sk=add("source",s["id"],s["display_text"] or s["text"] or s["title"] or s["gedcom_xref"]);edges.append((pk,sk,"cited by"))
    # deduplicate nodes/edges while retaining stable order
    nd={};[nd.setdefault(x["key"],x) for x in nodes]
    ed=[];seen=set()
    for e in edges:
        if e not in seen:seen.add(e);ed.append(e)
    return list(nd.values()),ed


def format_evidence_graph(db,pid):
    name=_name(db,pid);nodes,edges=evidence_graph(db,pid)
    by=defaultdict(int)
    for n in nodes:by[n["kind"]]+=1
    title=f"Knowledge Graph — {name}";L=[title,"="*len(title),""]
    L.append("Nodes")
    L.append("-----")
    for k in ("person","family","event","note","media","source"):
        if by[k]:L.append(f"  {k:<8} {by[k]}")
    L += ["","Edges","-----"]
    ec=defaultdict(int)
    for _,_,r in edges:ec[r]+=1
    for r,c in sorted(ec.items()):L.append(f"  {r:<14} {c}")
    L += ["","Evidence objects","----------------"]
    for n in nodes:
        if n["kind"]!="person":L.append(f"  {n['kind'].upper():<7} {n['label']}")
    return "\n".join(L)


def topic_people(db,text,limit=100):
    """People connected to a textual topic through events, notes, media or sources."""
    like=f"%{text}%";scores=defaultdict(lambda:{"score":0,"via":set()})
    for r in db.execute("SELECT DISTINCT person_id FROM events WHERE place_text LIKE ? OR value_text LIKE ? OR note_text LIKE ?",(like,like,like)):
        scores[r["person_id"]]["score"]+=3;scores[r["person_id"]]["via"].add("event")
    for r in db.execute("SELECT DISTINCT person_id FROM notes WHERE text LIKE ? AND person_id IS NOT NULL",(like,)):
        scores[r["person_id"]]["score"]+=4;scores[r["person_id"]]["via"].add("note")
    for r in db.execute("SELECT DISTINCT pm.person_id FROM person_media pm JOIN media m ON m.id=pm.media_id WHERE m.title LIKE ? OR m.file_path LIKE ?",(like,like)):
        scores[r["person_id"]]["score"]+=2;scores[r["person_id"]]["via"].add("media")
    for r in db.execute("SELECT DISTINCT e.person_id FROM event_media em JOIN events e ON e.id=em.event_id JOIN media m ON m.id=em.media_id WHERE m.title LIKE ? OR m.file_path LIKE ?",(like,like)):
        scores[r["person_id"]]["score"]+=2;scores[r["person_id"]]["via"].add("event media")
    for r in db.execute("SELECT DISTINCT ps.person_id FROM person_sources ps JOIN sources s ON s.id=ps.source_id WHERE s.display_text LIKE ? OR s.text LIKE ? OR s.title LIKE ?",(like,like,like)):
        scores[r["person_id"]]["score"]+=2;scores[r["person_id"]]["via"].add("source")
    for r in db.execute("SELECT DISTINCT e.person_id FROM event_sources es JOIN events e ON e.id=es.event_id JOIN sources s ON s.id=es.source_id WHERE s.display_text LIKE ? OR s.text LIKE ? OR s.title LIKE ?",(like,like,like)):
        scores[r["person_id"]]["score"]+=2;scores[r["person_id"]]["via"].add("event source")
    rows=[]
    for pid,d in scores.items():rows.append((d["score"],_name(db,pid),pid,", ".join(sorted(d["via"]))))
    rows.sort(key=lambda x:(-x[0],x[1]))
    return rows[:limit]


def format_topic_graph(db,text):
    rows=topic_people(db,text);title=f"Topic Graph — {text}";L=[title,"="*len(title)]
    if not rows:return "\n".join(L+["  (no connected people found)"])
    for score,name,pid,via in rows:L.append(f"  {name} [ID {pid}] — via {via} — relevance {score}")
    return "\n".join(L)
