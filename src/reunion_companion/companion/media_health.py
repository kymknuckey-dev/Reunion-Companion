from __future__ import annotations
from pathlib import Path
from collections import Counter

IMAGE_EXT={".jpg",".jpeg",".png",".gif",".webp",".tif",".tiff",".heic"}
DOC_EXT={".pdf",".doc",".docx",".rtf",".txt",".pages"}
LEGACY_EXT={".pict",".pct",".pic"}

def classify_media(m):
    ext=Path(m["file_path"]).expanduser().suffix.lower()
    if not bool(m["exists_on_disk"]): return "missing"
    if ext in LEGACY_EXT: return "legacy"
    if ext in IMAGE_EXT: return "image"
    if ext in DOC_EXT: return "document"
    return "unknown"

def media_health_data(db):
    rows=db.execute("SELECT * FROM media ORDER BY id").fetchall()
    classified=[(m,classify_media(m)) for m in rows]
    counts=Counter(c for _,c in classified)
    dup=db.execute("SELECT file_path,COUNT(*) n,GROUP_CONCAT(id) ids FROM media GROUP BY file_path HAVING COUNT(*)>1 ORDER BY n DESC,file_path").fetchall()
    return {"rows":rows,"counts":counts,"duplicates":dup,"legacy":[m for m,c in classified if c=="legacy"],"missing":[m for m,c in classified if c=="missing"],"unknown":[m for m,c in classified if c=="unknown"]}

def _used_by(db,media_id):
    people=db.execute("""SELECT DISTINCT p.display_name FROM people p WHERE p.id IN (
      SELECT person_id FROM person_media WHERE media_id=?
      UNION SELECT e.person_id FROM event_media em JOIN events e ON e.id=em.event_id WHERE em.media_id=?
      UNION SELECT fm2.person_id FROM family_media fm JOIN family_members fm2 ON fm2.family_id=fm.family_id WHERE fm.media_id=?
    ) ORDER BY p.display_name""",(media_id,media_id,media_id)).fetchall()
    return [r["display_name"] for r in people]

def format_media_health(db,detail_limit=25):
    d=media_health_data(db);c=d["counts"];total=len(d["rows"]);healthy=c["image"]+c["document"]
    score=round(100*healthy/total) if total else 100
    L=["Media Health","============","",f"Total media             {total}",f"Healthy/displayable     {healthy}",f"Images                  {c['image']}",f"Documents               {c['document']}",f"Legacy formats          {c['legacy']}",f"Missing files           {c['missing']}",f"Unknown formats         {c['unknown']}",f"Duplicate paths         {len(d['duplicates'])}",f"Archive health score    {score}%",""]
    if d["legacy"]:
        L += ["Legacy Media","------------"]
        for m in d["legacy"][:detail_limit]:
            used=", ".join(_used_by(db,m["id"])) or "unlinked"
            L += [f"  PICT/legacy: {m['title'] or Path(m['file_path']).name}",f"    Used by: {used}","    Recommendation: convert the original outside Companion, then update Reunion to the replacement."]
        L.append("")
    if d["missing"]:
        L += ["Missing Media","-------------"]
        for m in d["missing"][:detail_limit]:
            used=", ".join(_used_by(db,m["id"])) or "unlinked"
            L += [f"  {m['title'] or Path(m['file_path']).name}",f"    Used by: {used}",f"    Expected: {m['file_path']}"]
        L.append("")
    if d["unknown"]:
        L += ["Unknown Formats","---------------"]
        for m in d["unknown"][:detail_limit]: L.append(f"  {m['title'] or Path(m['file_path']).name} — {m['file_path']}")
        L.append("")
    if d["duplicates"]:
        L += ["Duplicate Paths","---------------"]
        for x in d["duplicates"][:detail_limit]: L.append(f"  {x['n']} × {x['file_path']} — media IDs {x['ids']}")
    return "\n".join(L)
