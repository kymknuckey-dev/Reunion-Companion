from __future__ import annotations

"""FFD 1.7 Build 1 — deterministic person knowledge assembly.

This module does not generate narrative prose.  It assembles the Reunion-derived
objects that are already present in Companion into a single, evidence-aware
person bundle that later conversational/narrative builds can consume.
"""

from collections import defaultdict
from typing import Any


def _rows(db, sql: str, args=()):
    return [dict(r) for r in db.execute(sql, args).fetchall()]


def _one(db, sql: str, args=()):
    r = db.execute(sql, args).fetchone()
    return dict(r) if r else None


def _source_label(source: dict[str, Any]) -> str:
    return (source.get("display_text") or source.get("text") or
            source.get("title") or source.get("gedcom_xref") or
            f"Source {source.get('id')}")


def _family_context(db, person_id: int):
    """Return family units plus relationship-labelled connected people."""
    family_ids = [r["family_id"] for r in db.execute(
        "SELECT DISTINCT family_id FROM family_members WHERE person_id=? ORDER BY family_id",
        (person_id,),
    )]
    families = []
    relationships = []
    seen_relationships = set()

    person = _one(db, "SELECT id,sex FROM people WHERE id=?", (person_id,)) or {}
    own_sex = (person.get("sex") or "").upper()

    for fid in family_ids:
        fam = _one(db, "SELECT * FROM families WHERE id=?", (fid,))
        members = _rows(db, """
            SELECT p.id,p.gedcom_xref,p.display_name,p.sex,fm.role
            FROM family_members fm JOIN people p ON p.id=fm.person_id
            WHERE fm.family_id=? ORDER BY p.id,fm.role
        """, (fid,))
        own_roles = {str(m["role"] or "").lower() for m in members if m["id"] == person_id}
        is_child_family = "child" in own_roles

        families.append({
            "id": fid,
            "gedcom_xref": fam.get("gedcom_xref") if fam else None,
            "marriage_date": fam.get("marriage_date") if fam else None,
            "marriage_place": fam.get("marriage_place") if fam else None,
            "person_roles": sorted(own_roles),
            "members": members,
        })

        for m in members:
            if m["id"] == person_id:
                continue
            role = str(m.get("role") or "").lower()
            sex = str(m.get("sex") or "").upper()
            label = None
            if is_child_family:
                if role in ("husband", "wife", "spouse"):
                    label = "Father" if sex == "M" else "Mother" if sex == "F" else "Parent"
                elif role == "child":
                    label = "Brother" if sex == "M" else "Sister" if sex == "F" else "Sibling"
            else:
                if role in ("husband", "wife", "spouse"):
                    label = "Spouse"
                elif role == "child":
                    label = "Son" if sex == "M" else "Daughter" if sex == "F" else "Child"
            if not label:
                continue
            key = (m["id"], label, fid)
            if key in seen_relationships:
                continue
            seen_relationships.add(key)
            relationships.append({
                "relationship": label,
                "person_id": m["id"],
                "display_name": m["display_name"],
                "gedcom_xref": m["gedcom_xref"],
                "family_id": fid,
            })

    order = {"Father": 0, "Mother": 1, "Parent": 2, "Spouse": 3,
             "Son": 4, "Daughter": 4, "Child": 4,
             "Brother": 5, "Sister": 5, "Sibling": 5}
    relationships.sort(key=lambda r: (order.get(r["relationship"], 9), r["display_name"], r["person_id"]))
    return families, relationships


def _source_map(db, person_id: int, events, notes, families):
    """Collect linked sources without flattening away their ownership context."""
    linked = defaultdict(list)

    def add(scope: str, owner_id: int, sql: str, args):
        for r in _rows(db, sql, args):
            r["label"] = _source_label(r)
            linked[(scope, owner_id)].append(r)

    add("person", person_id, """
        SELECT s.*,ps.relation FROM person_sources ps JOIN sources s ON s.id=ps.source_id
        WHERE ps.person_id=? ORDER BY s.id
    """, (person_id,))
    for e in events:
        add("event", e["id"], """
            SELECT s.*,es.relation FROM event_sources es JOIN sources s ON s.id=es.source_id
            WHERE es.event_id=? ORDER BY s.id
        """, (e["id"],))
    for n in notes:
        add("note", n["id"], """
            SELECT s.*,ns.relation FROM note_sources ns JOIN sources s ON s.id=ns.source_id
            WHERE ns.note_id=? ORDER BY s.id
        """, (n["id"],))
    for f in families:
        add("family", f["id"], """
            SELECT s.*,fs.relation FROM family_sources fs JOIN sources s ON s.id=fs.source_id
            WHERE fs.family_id=? ORDER BY s.id
        """, (f["id"],))

    citations = _rows(db, """
        SELECT c.*,s.gedcom_xref AS source_xref,s.title AS source_title,
               s.text AS source_text,s.source_type,s.display_text AS source_display_text
        FROM citations c JOIN sources s ON s.id=c.source_id
        WHERE c.person_id=?
           OR c.event_id IN (SELECT id FROM events WHERE person_id=?)
           OR c.note_id IN (SELECT id FROM notes WHERE person_id=?)
           OR c.family_id IN (SELECT family_id FROM family_members WHERE person_id=?)
        ORDER BY c.id
    """, (person_id, person_id, person_id, person_id))

    unique = {}
    for rows in linked.values():
        for s in rows:
            unique[s["id"]] = {k: v for k, v in s.items() if k != "relation"}
    for c in citations:
        sid = c["source_id"]
        unique.setdefault(sid, {
            "id": sid,
            "gedcom_xref": c.get("source_xref"),
            "title": c.get("source_title"),
            "text": c.get("source_text"),
            "source_type": c.get("source_type"),
            "display_text": c.get("source_display_text"),
            "label": c.get("source_display_text") or c.get("source_text") or c.get("source_title") or c.get("source_xref"),
        })

    return linked, citations, [unique[k] for k in sorted(unique)]


def _media(db, person_id: int, events, families):
    """Collect direct, event and family media with attachment provenance."""
    out = []
    seen = set()

    def add(scope: str, owner_id: int, sql: str, args):
        for r in _rows(db, sql, args):
            key = (scope, owner_id, r["id"], r.get("relation"))
            if key in seen:
                continue
            seen.add(key)
            r["owner_scope"] = scope
            r["owner_id"] = owner_id
            out.append(r)

    add("person", person_id, """
        SELECT m.*,pm.relation FROM person_media pm JOIN media m ON m.id=pm.media_id
        WHERE pm.person_id=? ORDER BY m.id
    """, (person_id,))
    for e in events:
        add("event", e["id"], """
            SELECT m.*,em.relation FROM event_media em JOIN media m ON m.id=em.media_id
            WHERE em.event_id=? ORDER BY m.id
        """, (e["id"],))
    for f in families:
        add("family", f["id"], """
            SELECT m.*,fm.relation FROM family_media fm JOIN media m ON m.id=fm.media_id
            WHERE fm.family_id=? ORDER BY m.id
        """, (f["id"],))
    return out


def assemble_person_knowledge(db, person_id: int) -> dict[str, Any] | None:
    """Assemble all currently decoded Reunion knowledge for one person.

    The result is deliberately structured and deterministic.  No inference is
    promoted to fact and no narrative text is invented here.
    """
    person = _one(db, "SELECT * FROM people WHERE id=?", (person_id,))
    if not person:
        return None

    events = _rows(db, "SELECT * FROM events WHERE person_id=? ORDER BY id", (person_id,))
    notes = _rows(db, "SELECT * FROM notes WHERE person_id=? ORDER BY id", (person_id,))
    families, relationships = _family_context(db, person_id)
    source_links, citations, sources = _source_map(db, person_id, events, notes, families)
    media = _media(db, person_id, events, families)

    # Attach sources to their owning objects while keeping a top-level evidence index.
    for e in events:
        e["sources"] = source_links.get(("event", e["id"]), [])
    for n in notes:
        n["sources"] = source_links.get(("note", n["id"]), [])
    for f in families:
        f["sources"] = source_links.get(("family", f["id"]), [])

    places = []
    seen_places = set()
    for e in events:
        place = (e.get("place_text") or "").strip()
        if place and place not in seen_places:
            seen_places.add(place)
            places.append({"name": place, "event_ids": [x["id"] for x in events if (x.get("place_text") or "").strip() == place]})
    for f in families:
        place = (f.get("marriage_place") or "").strip()
        if place and place not in seen_places:
            seen_places.add(place)
            places.append({"name": place, "family_ids": [x["id"] for x in families if (x.get("marriage_place") or "").strip() == place]})

    direct_sources = source_links.get(("person", person_id), [])
    counts = {
        "events": len(events),
        "notes": len(notes),
        "relationships": len(relationships),
        "families": len(families),
        "places": len(places),
        "sources": len(sources),
        "citations": len(citations),
        "media": len(media),
    }

    return {
        "person": person,
        "events": events,
        "notes": notes,
        "relationships": relationships,
        "families": families,
        "places": places,
        "media": media,
        "sources": sources,
        "direct_sources": direct_sources,
        "citations": citations,
        "counts": counts,
        "assembly": {
            "build": "FFD 1.7 Build 1",
            "mode": "deterministic",
            "narrative_generated": False,
            "principle": "Assembled from imported Reunion objects; missing information remains missing.",
        },
    }


def knowledge_inventory_text(db, person_id: int) -> str:
    """Small diagnostic representation for verification and future CLI/UI hooks."""
    k = assemble_person_knowledge(db, person_id)
    if not k:
        return f"Person {person_id} not found."
    name = k["person"]["display_name"]
    c = k["counts"]
    lines = [f"Person Knowledge — {name}", "=" * (19 + len(name))]
    for label in ("events", "notes", "relationships", "families", "places", "sources", "citations", "media"):
        lines.append(f"{label.title():<15} {c[label]}")
    lines += ["", "Assembly is deterministic; no narrative has been generated."]
    return "\n".join(lines)
