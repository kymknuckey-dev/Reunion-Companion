from __future__ import annotations
from .intelligence import person_quality
from .evidence_engine import overall_evidence_score

def research_opportunities(db,pid):
    q=person_quality(db,pid);rows=[]
    for typ,msg,snip in q["cautions"]:
        priority="High" if typ in ("Birth","Death","Military Service","Research") else "Medium"
        rows.append((priority,typ,msg,snip))
    for typ,vals in q["conflicts"]:
        rows.append(("High",typ,"Conflicting core-event values require review"," | ".join(" — ".join(x for x in v if x) for v in vals)))
    missing=db.execute("""SELECT m.* FROM media m WHERE m.exists_on_disk=0 AND m.id IN (
        SELECT media_id FROM person_media WHERE person_id=?
        UNION SELECT em.media_id FROM event_media em JOIN events e ON e.id=em.event_id WHERE e.person_id=?
        UNION SELECT fm.media_id FROM family_media fm JOIN family_members fmem ON fmem.family_id=fm.family_id WHERE fmem.person_id=?
    ) ORDER BY m.id""",(pid,pid,pid)).fetchall()
    for m in missing:
        rows.append(("Medium","Media","Referenced media is missing on disk",m["title"] or m["file_path"]))
    rank={"High":0,"Medium":1,"Low":2}
    rows.sort(key=lambda x:(rank[x[0]],x[1],x[2]))
    return rows

def format_improve(db,pid):
    p=db.execute("SELECT display_name FROM people WHERE id=?",(pid,)).fetchone()
    rows=research_opportunities(db,pid)
    title=f"Research Opportunities — {p['display_name']}";L=[title,"="*len(title),
        f"Visible evidence score: {overall_evidence_score(db,pid)}%",""]
    if not rows:
        L.append("No obvious improvement opportunities detected from the imported snapshot.")
    else:
        for priority,area,msg,detail in rows:
            L.append(f"[{priority}] {area}")
            L.append(f"  {msg}")
            if detail:L.append(f"  {detail}")
            L.append("")
    L += ["Interpretation","--------------",
          "These are prompts for review. They identify missing links, conflicts or unavailable files visible to the Companion; they do not assert that Reunion's information is historically wrong."]
    return "\n".join(L)
