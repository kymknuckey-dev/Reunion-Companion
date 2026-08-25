from __future__ import annotations
from .external_evidence_scan import SOURCE_RYERSON, enqueue_death_research_candidates, run_one_scan, scan_summary

META_ENABLED="ryerson_runner_enabled"

def _meta_get(db,key,default=""):
    row=db.execute("SELECT value FROM meta WHERE key=?",(key,)).fetchone()
    return row["value"] if row else default

def _meta_set(db,key,value):
    db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",(key,value)); db.commit()

def runner_enabled(db):
    return _meta_get(db,META_ENABLED,"0")=="1"

def start_runner(db):
    added=enqueue_death_research_candidates(db,SOURCE_RYERSON)
    _meta_set(db,META_ENABLED,"1")
    out=runner_status(db); out["newly_queued"]=added; return out

def pause_runner(db):
    _meta_set(db,META_ENABLED,"0")
    return runner_status(db)

def runner_status(db):
    summary=scan_summary(db,SOURCE_RYERSON); c=summary["counts"]
    return {"enabled":runner_enabled(db),"source_name":SOURCE_RYERSON,"total":summary["total"],
            "queued":c.get("queued",0),"searching":c.get("searching",0),
            "retry_wait":c.get("retry_wait",0),"findings":c.get("succeeded_with_findings",0),
            "no_match":c.get("succeeded_no_match",0),"failed":c.get("failed",0)}

def runner_tick(db,search_fn):
    if not runner_enabled(db): return {"status":"paused"}
    return run_one_scan(db,search_fn,source_name=SOURCE_RYERSON)
