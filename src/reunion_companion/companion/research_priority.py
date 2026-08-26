from __future__ import annotations

from .knowledge_graph import relationship_path
from .relationship_engine import interpret_relationship


def default_focus_person(db):
    row=db.execute(
        "SELECT id,display_name FROM people WHERE lower(display_name)=lower(?) ORDER BY id LIMIT 1",
        ("Mervyn Neil Knuckey",),
    ).fetchone()
    if row:
        return row
    return db.execute("SELECT id,display_name FROM people ORDER BY id LIMIT 1").fetchone()


def resolve_focus_person(db, focus_id=None):
    if focus_id:
        try:
            row=db.execute("SELECT id,display_name FROM people WHERE id=?",(int(focus_id),)).fetchone()
        except Exception:
            row=None
        if row:
            return row
    return default_focus_person(db)


def relationship_priority(db, focus_id, person_id, max_depth=12, adj=None):
    focus_id=int(focus_id); person_id=int(person_id)
    path=relationship_path(db,focus_id,person_id,max_depth,adj=adj)
    if path is None:
        return {"distance":None,"label":"Relationship not established","confidence":"none"}
    rr=interpret_relationship(db,focus_id,person_id,max_depth,adj=adj)
    label=rr.reciprocal if focus_id!=person_id else "same person"
    return {"distance":len(path),"label":label,"confidence":rr.confidence}


def _relationship_distance_map(db, focus_id, max_depth=12):
    from collections import deque
    from .knowledge_graph import adjacency
    focus_id=int(focus_id)
    adj=adjacency(db)
    distances={focus_id:0}
    q=deque([focus_id])
    while q:
        current=q.popleft()
        distance=distances[current]
        if distance>=max_depth:
            continue
        for edge in adj.get(current,()):
            if edge.right in distances:
                continue
            distances[edge.right]=distance+1
            q.append(edge.right)
    return distances


def priority_map(db, focus_id, person_ids, max_depth=12):
    ids=sorted({int(x) for x in person_ids if x not in (None,"")})
    distances=_relationship_distance_map(db,focus_id,max_depth)
    return {
        pid:{
            "distance":distances.get(pid),
            "label":"same person" if pid==int(focus_id) else (
                f"Related — {distances[pid]} step{'s' if distances[pid]!=1 else ''} from research focus"
                if pid in distances else "Relationship not established"
            ),
            "confidence":"structural" if pid in distances else "none",
        }
        for pid in ids
    }


def enrich_priority_labels(db, focus_id, rels, person_ids, max_depth=12, adj=None):
    from .knowledge_graph import adjacency
    adj=adj if adj is not None else adjacency(db)
    for raw_pid in person_ids:
        pid=int(raw_pid)
        if pid not in rels or rels[pid]["distance"] is None:
            continue
        if pid==int(focus_id):
            rels[pid]={"distance":0,"label":"same person","confidence":"high"}
            continue
        rels[pid]=relationship_priority(db,focus_id,pid,max_depth,adj=adj)
    return rels


def sort_grouped_people(db, focus_id, grouped):
    rels=priority_map(db,focus_id,[pid for pid,_ in grouped])
    grouped=sorted(
        grouped,
        key=lambda item:(
            rels[item[0]]["distance"] is None,
            rels[item[0]]["distance"] if rels[item[0]]["distance"] is not None else 10**9,
            str(item[1][0]["display_name"] or "").casefold() if "display_name" in item[1][0].keys() else "",
        ),
    )
    enrich_priority_labels(db,focus_id,rels,[pid for pid,_ in grouped[:20]])
    return grouped,rels


def sort_rows_by_focus(db, focus_id, rows, person_key):
    rels=priority_map(db,focus_id,[r[person_key] for r in rows])
    def key(row):
        pid=int(row[person_key]); rel=rels[pid]
        name=str(row["display_name"] or "").casefold() if "display_name" in row.keys() else ""
        return (rel["distance"] is None, rel["distance"] if rel["distance"] is not None else 10**9, name)
    ordered=sorted(rows,key=key)
    enrich_priority_labels(db,focus_id,rels,[r[person_key] for r in ordered[:8]])
    return ordered,rels


def _event_value(row,*names):
    if row is None:
        return ""
    keys=set(row.keys())
    for name in names:
        if name in keys and row[name] not in (None,""):
            return str(row[name]).strip()
    return ""


def death_research_semantics(db, person_id):
    death=db.execute(
        "SELECT * FROM events WHERE person_id=? AND lower(event_type)='death' ORDER BY id LIMIT 1",
        (int(person_id),),
    ).fetchone()
    if death is None:
        return {"state":"missing","label":"Death missing"}

    date=_event_value(death,"date_text","event_date","date","date_value")
    place=_event_value(death,"place","place_text","place_name","location")
    has_useful_fact=bool(date or place)

    sourced=db.execute("SELECT 1 FROM event_sources WHERE event_id=? LIMIT 1",(death["id"],)).fetchone() is not None
    media=db.execute("SELECT 1 FROM event_media WHERE event_id=? LIMIT 1",(death["id"],)).fetchone() is not None

    if has_useful_fact and not (sourced or media):
        return {"state":"needs_evidence","label":"Death needs evidence"}
    return {"state":"details_incomplete","label":"Death details incomplete"}
