from __future__ import annotations
from pathlib import Path
import re
from .discovery import relationship_connections

IMAGE_EXT={".jpg",".jpeg",".png",".gif",".webp"}
PDF_EXT={".pdf"}

def person(db,pid):
    return db.execute("SELECT * FROM people WHERE id=?",(pid,)).fetchone()

def family_members(db,family_id):
    return db.execute("""SELECT p.*,fm.role FROM family_members fm
        JOIN people p ON p.id=fm.person_id
        WHERE fm.family_id=? ORDER BY CASE fm.role WHEN 'Husband' THEN 1 WHEN 'Wife' THEN 2 ELSE 3 END,p.id""",
        (family_id,)).fetchall()

def spouse_families(db,pid):
    return db.execute("""SELECT f.*,fm.role FROM families f
        JOIN family_members fm ON fm.family_id=f.id
        WHERE fm.person_id=? AND fm.role IN ('Husband','Wife')
        ORDER BY f.id""",(pid,)).fetchall()

def resolve_family_for_people(db,pid,spouse_id=None):
    fams=spouse_families(db,pid)
    if spouse_id is not None:
        for f in fams:
            hit=db.execute("SELECT 1 FROM family_members WHERE family_id=? AND person_id=? AND role IN ('Husband','Wife')",
                           (f["id"],spouse_id)).fetchone()
            if hit:return f
        return None
    if len(fams)==1:return fams[0]
    return None

def family_partners(db,family_id):
    mem=family_members(db,family_id)
    husband=next((x for x in mem if x["role"]=="Husband"),None)
    wife=next((x for x in mem if x["role"]=="Wife"),None)
    return husband,wife

def children(db,family_id):
    return db.execute("""SELECT p.*,fm.role FROM family_members fm JOIN people p ON p.id=fm.person_id
        WHERE fm.family_id=? AND fm.role='Child' ORDER BY p.id""",(family_id,)).fetchall()

def _event(db,pid,typ):
    return db.execute("""SELECT * FROM events WHERE person_id=? AND event_type=?
        ORDER BY CASE WHEN date_text IS NULL OR date_text='' THEN 1 ELSE 0 END,id LIMIT 1""",(pid,typ)).fetchone()

def life_dates(db,pid):
    b=_event(db,pid,"Birth");d=_event(db,pid,"Death")
    return {
        "birth":b["date_text"] if b else None,
        "birth_place":b["place_text"] if b else None,
        "death":d["date_text"] if d else None,
        "death_place":d["place_text"] if d else None,
    }

def person_events(db,pid):
    return db.execute("SELECT * FROM events WHERE person_id=? AND event_type<>'Changed' ORDER BY id",(pid,)).fetchall()

def person_notes(db,pid):
    return db.execute("SELECT * FROM notes WHERE person_id=? ORDER BY id",(pid,)).fetchall()

def person_sources(db,pid):
    return db.execute("""SELECT DISTINCT s.* FROM sources s WHERE s.id IN (
        SELECT source_id FROM person_sources WHERE person_id=?
        UNION SELECT es.source_id FROM event_sources es JOIN events e ON e.id=es.event_id WHERE e.person_id=?
        UNION SELECT ns.source_id FROM note_sources ns JOIN notes n ON n.id=ns.note_id WHERE n.person_id=?
        UNION SELECT fs.source_id FROM family_sources fs JOIN family_members fm ON fm.family_id=fs.family_id WHERE fm.person_id=?
    ) ORDER BY s.id""",(pid,pid,pid,pid)).fetchall()

def family_sources(db,family_id):
    return db.execute("""SELECT DISTINCT s.* FROM sources s JOIN family_sources fs ON fs.source_id=s.id
        WHERE fs.family_id=? ORDER BY s.id""",(family_id,)).fetchall()

def _media_union(db,pid):
    return db.execute("""SELECT DISTINCT m.* FROM media m WHERE m.id IN (
        SELECT media_id FROM person_media WHERE person_id=?
        UNION SELECT em.media_id FROM event_media em JOIN events e ON e.id=em.event_id WHERE e.person_id=?
    ) ORDER BY m.id""",(pid,pid)).fetchall()

def person_media(db,pid):
    return _media_union(db,pid)

def family_media(db,family_id):
    return db.execute("""SELECT DISTINCT m.* FROM media m JOIN family_media fm ON fm.media_id=m.id
        WHERE fm.family_id=? ORDER BY m.id""",(family_id,)).fetchall()

def _title(m):
    return (m["title"] or Path(m["file_path"]).name or "").strip()

def media_kind(m):
    ext=Path(m["file_path"]).suffix.lower()
    t=_title(m).lower()
    if ext in IMAGE_EXT:
        if any(x in t for x in ("birth certificate","death certificate","marriage certificate","wedding certificate","burial","certificate","extract")):
            return "document-image"
        if any(x in t for x in ("wedding","marriage","wed ")):
            return "wedding-photo"
        return "photo"
    if ext in PDF_EXT:
        if any(x in t for x in ("marriage","wedding")):return "marriage-document"
        if "birth" in t:return "birth-document"
        if "death" in t:return "death-document"
        if "military" in t or "service" in t:return "military-document"
        return "document"
    if ext in (".pict",".pct",".pic"):return "legacy"
    return "other"

def family_publication_media(db,family_id,husband_id=None,wife_id=None):
    family=list(family_media(db,family_id))
    related=list(family)
    for pid in (husband_id,wife_id):
        if pid:
            related.extend(person_media(db,pid))
    # stable de-duplication
    seen=set();items=[]
    for m in related:
        if m["id"] in seen:continue
        seen.add(m["id"]);items.append(m)
    wedding_photos=[m for m in items if media_kind(m)=="wedding-photo"]
    marriage_docs=[m for m in items if media_kind(m)=="marriage-document"]
    return family,wedding_photos,marriage_docs

def person_document_groups(db,pid):
    groups={"portrait":[],"birth":[],"death":[],"military":[],"other-documents":[],"other-photos":[],"legacy":[]}
    for m in person_media(db,pid):
        k=media_kind(m)
        title=_title(m).lower()
        if k=="legacy":groups["legacy"].append(m)
        elif k=="birth-document" or (k=="document-image" and "birth" in title):groups["birth"].append(m)
        elif k=="death-document" or (k=="document-image" and ("death" in title or "burial" in title)):groups["death"].append(m)
        elif k=="military-document":groups["military"].append(m)
        elif k in ("document","document-image","marriage-document"):groups["other-documents"].append(m)
        elif k=="photo":
            groups["portrait"].append(m) if not groups["portrait"] else groups["other-photos"].append(m)
        elif k=="wedding-photo":
            # Family wedding photographs are placed in the marriage section, not duplicated on person pages.
            pass
        else:groups["other-documents"].append(m)
    return groups

def parent_couple(db,pid):
    c=relationship_connections(db,pid)
    return c["parents"][:2]

def descendant_rows(db,pid,generations=4):
    """Nested genealogy rows used by the compact book chart."""
    rows=[]
    def walk(cur,level,path):
        if level>generations:return
        if cur in path:return
        p=person(db,cur)
        if not p:return
        dates=life_dates(db,cur)
        spouses=relationship_connections(db,cur)["spouses"]
        rows.append({"id":cur,"name":p["display_name"],"level":level,
                     "birth":dates["birth"],"death":dates["death"],
                     "spouses":[{"id":sp["id"],"name":sp["display_name"]} for sp in spouses]})
        if level==generations:return
        for ch in relationship_connections(db,cur)["children"]:
            walk(ch["id"],level+1,path|{cur})
    walk(pid,0,set())
    return rows

def family_context_chart(db,husband_id,wife_id,generations=3):
    return {
      "husband_parents":parent_couple(db,husband_id) if husband_id else [],
      "wife_parents":parent_couple(db,wife_id) if wife_id else [],
      "husband":person(db,husband_id) if husband_id else None,
      "wife":person(db,wife_id) if wife_id else None,
      "descendants":descendant_rows(db,husband_id or wife_id,generations) if (husband_id or wife_id) else []
    }

def family_overview(db,family_id):
    f=db.execute("SELECT * FROM families WHERE id=?",(family_id,)).fetchone()
    husband,wife=family_partners(db,family_id);kids=children(db,family_id)
    familym,wedding,marriage_docs=family_publication_media(db,family_id,
        husband["id"] if husband else None,wife["id"] if wife else None)
    known_desc=set()
    for root in [x for x in (husband,wife) if x]:
        for r in descendant_rows(db,root["id"],8):
            if r["level"]>0:known_desc.add(r["id"])
    media_ids=set(m["id"] for m in familym)
    for p in (husband,wife):
        if p:media_ids.update(m["id"] for m in person_media(db,p["id"]))
    source_ids=set(s["id"] for s in family_sources(db,family_id))
    for p in (husband,wife):
        if p:source_ids.update(s["id"] for s in person_sources(db,p["id"]))
    return {
      "family":f,"husband":husband,"wife":wife,"children":kids,
      "children_count":len(kids),"known_descendants":len(known_desc),
      "media_count":len(media_ids),"source_count":len(source_ids),
      "wedding_photos":wedding,"marriage_documents":marriage_docs,
    }
