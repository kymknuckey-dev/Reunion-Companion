from __future__ import annotations
from .external_evidence_scan import SOURCE_RYERSON, enqueue_death_research_candidates, run_one_scan, scan_summary

META_ENABLED="ryerson_runner_enabled"
META_COOLDOWN_UNTIL="ryerson_runner_cooldown_until"

def _meta_get(db,key,default=""):
    row=db.execute("SELECT value FROM meta WHERE key=?",(key,)).fetchone()
    return row["value"] if row else default

def _meta_set(db,key,value):
    db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",(key,value)); db.commit()

def _parse_iso(value):
    if not value:
        return None
    from datetime import datetime
    return datetime.fromisoformat(value)

def source_cooldown_until(db):
    return _parse_iso(_meta_get(db,META_COOLDOWN_UNTIL,""))

def _set_source_cooldown(db,value):
    _meta_set(db,META_COOLDOWN_UNTIL,value or "")

def source_waiting(db, now=None):
    from datetime import datetime, timezone
    now=now or datetime.now(timezone.utc)
    until=source_cooldown_until(db)
    return bool(until and until > now)

def runner_enabled(db):
    return _meta_get(db,META_ENABLED,"0")=="1"

def start_runner(db):
    added=enqueue_death_research_candidates(db,SOURCE_RYERSON)
    # Backfill any stored findings that pre-date the live review handoff.
    # The bridge is idempotent and preserves existing review decisions.
    from .ryerson_person_finding_bridge import materialize_person_level_ryerson_findings
    materialize_person_level_ryerson_findings(db)
    _meta_set(db,META_ENABLED,"1")
    out=runner_status(db); out["newly_queued"]=added; return out

def pause_runner(db):
    _meta_set(db,META_ENABLED,"0")
    return runner_status(db)

def runner_status(db):
    summary=scan_summary(db,SOURCE_RYERSON); c=summary["counts"]
    until=source_cooldown_until(db)
    return {"enabled":runner_enabled(db),"source_name":SOURCE_RYERSON,"total":summary["total"],
            "queued":c.get("queued",0),"searching":c.get("searching",0),
            "retry_wait":c.get("retry_wait",0),"findings":c.get("succeeded_with_findings",0),
            "no_match":c.get("succeeded_no_match",0),"failed":c.get("failed",0),
            "source_waiting":source_waiting(db),
            "cooldown_until":until.isoformat() if until else None}

def runner_tick(db,search_fn,now=None):
    from datetime import datetime, timezone
    now=now or datetime.now(timezone.utc)
    if not runner_enabled(db):
        return {"status":"paused"}
    if source_waiting(db,now):
        until=source_cooldown_until(db)
        return {"status":"source_wait","next_retry_at":until.isoformat() if until else None}
    result=run_one_scan(db,search_fn,source_name=SOURCE_RYERSON,now=now)
    if result.get("status")=="retry_wait":
        _set_source_cooldown(db,result.get("next_retry_at"))
    elif result.get("status") in ("succeeded_no_match","succeeded_with_findings"):
        _set_source_cooldown(db,"")
        if result.get("status")=="succeeded_with_findings":
            row=db.execute(
                "SELECT person_gedcom_xref FROM companion_external_scan_queue WHERE id=?",
                (result.get("queue_id"),),
            ).fetchone()
            if row and row["person_gedcom_xref"]:
                from .ryerson_person_finding_bridge import materialize_person_level_ryerson_findings
                materialize_person_level_ryerson_findings(db,row["person_gedcom_xref"])
    return result

def recover_transport_failures(db, source_name=SOURCE_RYERSON):
    """Requeue failures caused by transport/form discovery, not evidence semantics."""
    recoverable=(
        "surname field not found",
        "given name field not found",
        "state field not found",
    )
    rows=db.execute(
        "SELECT id,last_error FROM companion_external_scan_queue WHERE source_name=? AND status='failed'",
        (source_name,),
    ).fetchall()
    ids=[r["id"] for r in rows if (r["last_error"] or "").casefold() in recoverable]
    for qid in ids:
        db.execute(
            "UPDATE companion_external_scan_queue SET status='queued', attempts=0, last_error=NULL, "
            "last_attempt_at=NULL, next_retry_at=NULL, completed_at=NULL, result_count=0 WHERE id=?",
            (qid,),
        )
    db.commit()
    return len(ids)


def recover_interrupted_runner_state(db, source_name=SOURCE_RYERSON, now=None):
    """Recover queue state that cannot belong to a live worker after restart.

    A row left as ``searching`` belonged to the previous process and is safe to
    return to the queue. Expired retry waits are also made immediately runnable.
    Completed and failed evidence decisions are never changed.
    """
    from datetime import datetime, timezone
    now=now or datetime.now(timezone.utc)

    rows=db.execute(
        "SELECT id,status,attempts,next_retry_at FROM companion_external_scan_queue "
        "WHERE source_name=? AND status IN ('searching','retry_wait')",
        (source_name,),
    ).fetchall()
    recovered=0
    for row in rows:
        should_requeue=row["status"]=="searching"
        if row["status"]=="retry_wait":
            due=_parse_iso(row["next_retry_at"])
            should_requeue=due is None or due<=now
        if not should_requeue:
            continue
        attempts=int(row["attempts"] or 0)
        if row["status"]=="searching" and attempts:
            attempts-=1
        db.execute(
            "UPDATE companion_external_scan_queue "
            "SET status='queued', attempts=?, last_error=NULL, next_retry_at=NULL, "
            "updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (attempts,row["id"]),
        )
        recovered+=1

    until=source_cooldown_until(db)
    if until is not None and until<=now:
        db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",(META_COOLDOWN_UNTIL,""))
    db.commit()
    return recovered

def live_ryerson_search(profile):
    from .ryerson_adapter import search_ryerson
    from .ryerson_safari_transport import safari_fetch
    return search_ryerson(profile,safari_fetch)

def live_runner_tick(db,now=None):
    return runner_tick(db,live_ryerson_search,now=now)

def start_background_runner(db_path, *, interval_seconds=90, poll_seconds=10):
    import threading
    import time

    def worker():
        from .database import connect
        # Refresh the review index once at app start so discoveries materialised
        # before confidence propagation was introduced receive their stored score.
        try:
            db=connect(db_path)
            try:
                from .ryerson_person_finding_bridge import materialize_person_level_ryerson_findings
                materialize_person_level_ryerson_findings(db)
            finally:
                db.close()
        except Exception:
            pass
        next_allowed=0.0
        while True:
            try:
                db=connect(db_path)
                try:
                    enabled=runner_enabled(db)
                    waiting=source_waiting(db)
                finally:
                    db.close()

                now_mono=time.monotonic()
                if enabled and not waiting and now_mono >= next_allowed:
                    db=connect(db_path)
                    try:
                        live_runner_tick(db)
                    finally:
                        db.close()
                    next_allowed=time.monotonic()+interval_seconds
            except Exception:
                next_allowed=time.monotonic()+interval_seconds
            time.sleep(poll_seconds)

    thread=threading.Thread(target=worker,name="ReunionCompanion-RyersonRunner",daemon=True)
    thread.start()
    return thread
