from __future__ import annotations
from .research_engine import research_opportunities
from .evidence_engine import overall_evidence_score

def audit_person(db,pid):
    p=db.execute("SELECT display_name FROM people WHERE id=?",(pid,)).fetchone()
    opp=research_opportunities(db,pid)
    high=sum(1 for x in opp if x[0]=="High")
    med=sum(1 for x in opp if x[0]=="Medium")
    evidence=overall_evidence_score(db,pid)
    completeness=max(0,min(100,round(evidence*0.7 + max(0,100-high*15-med*5)*0.3)))
    return {"name":p["display_name"],"issues":opp,"evidence":evidence,"completeness":completeness}

def format_audit(db,pid):
    a=audit_person(db,pid);title=f"Genealogy Audit — {a['name']}";L=[title,"="*len(title),
        f"Evidence linkage: {a['evidence']}%",f"Research readiness: {a['completeness']}%",""]
    if not a["issues"]:
        L.append("No obvious audit warnings detected.")
    else:
        L.append("Warnings / review items")
        L.append("-----------------------")
        for priority,area,msg,detail in a["issues"]:
            L.append(f"  {priority}: {area} — {msg}")
            if detail:L.append(f"      {detail}")
    L += ["","Audit scope","-----------",
          "This audit checks consistency and visible supporting links in the Companion snapshot. It is not a substitute for reviewing original historical records."]
    return "\n".join(L)
