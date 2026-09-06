from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .external_evidence import add_external_evidence
from .external_evidence_matcher import (
    match_external_evidence,
    person_identity_profile,
    ryerson_death_candidates,
)

SOURCE_RYERSON = "Ryerson"

class SourceBusyError(RuntimeError):
    pass

class SourceSearchError(RuntimeError):
    pass

def _utcnow():
    return datetime.now(timezone.utc)

def _iso(dt):
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()

def _parse_iso(value):
    return datetime.fromisoformat(value) if value else None

def backoff_seconds(attempts):
    attempts=max(1,int(attempts))
    return min(21600,300*(2**(attempts-1)))

def enqueue_death_research_candidates(db, source_name=SOURCE_RYERSON):
    added=0
    for row in ryerson_death_candidates(db):
        xref=row.get("gedcom_xref")
        if not xref:
            continue
        cur=db.execute(
            "INSERT OR IGNORE INTO companion_external_scan_queue("
            "source_name,person_gedcom_xref,person_name_snapshot,status"
            ") VALUES(?,?,?,'queued')",
            (source_name,xref,row.get("display_name")),
        )
        added+=int(cur.rowcount or 0)
    db.commit()
    return added

def queue_rows(db, source_name=SOURCE_RYERSON):
    return db.execute(
        "SELECT * FROM companion_external_scan_queue "
        "WHERE source_name=? ORDER BY id",
        (source_name,),
    ).fetchall()

def next_runnable_scan(db, source_name=SOURCE_RYERSON, now=None):
    now=now or _utcnow()
    rows=db.execute(
        "SELECT * FROM companion_external_scan_queue "
        "WHERE source_name=? AND status IN ('queued','retry_wait') ORDER BY id",
        (source_name,),
    ).fetchall()
    for row in rows:
        if row["status"]=="queued":
            return row
        due=_parse_iso(row["next_retry_at"])
        if due is None or due<=now:
            return row
    return None

def _set_status(db, queue_id, *, status, attempts=None, last_error=None,
                last_attempt_at=None, next_retry_at=None, completed_at=None,
                result_count=None, coverage_scope=None, coverage_completed_at=None):
    fields=["status=?","updated_at=CURRENT_TIMESTAMP"]
    vals=[status]
    supplied={
        "attempts": attempts,
        "last_error": last_error,
        "last_attempt_at": _iso(last_attempt_at) if last_attempt_at else None,
        "next_retry_at": _iso(next_retry_at) if next_retry_at else None,
        "completed_at": _iso(completed_at) if completed_at else None,
        "result_count": result_count,
        "coverage_scope": coverage_scope,
        "coverage_completed_at": _iso(coverage_completed_at) if coverage_completed_at else None,
    }
    for name,value in supplied.items():
        if value is not None:
            fields.append(f"{name}=?")
            vals.append(value)
    vals.append(queue_id)
    db.execute(
        f"UPDATE companion_external_scan_queue SET {','.join(fields)} WHERE id=?",
        vals,
    )
    db.commit()

def run_one_scan(db, search_fn, *, source_name=SOURCE_RYERSON, now=None):
    now=now or _utcnow()
    row=next_runnable_scan(db,source_name,now)
    if row is None:
        return {"status":"idle"}

    attempts=int(row["attempts"] or 0)+1
    _set_status(
        db,row["id"],status="searching",attempts=attempts,last_attempt_at=now
    )

    person=db.execute(
        "SELECT id FROM people WHERE gedcom_xref=?",
        (row["person_gedcom_xref"],),
    ).fetchone()
    if not person:
        _set_status(
            db,row["id"],status="failed",attempts=attempts,
            last_error="Person is not present in the current Reunion snapshot",
            last_attempt_at=now,
        )
        return {"status":"failed","queue_id":row["id"]}

    profile=person_identity_profile(db,person["id"])

    try:
        candidates=search_fn(profile) or []
    except SourceBusyError as exc:
        retry=now+timedelta(seconds=backoff_seconds(attempts))
        _set_status(
            db,row["id"],status="retry_wait",attempts=attempts,
            last_error=str(exc) or "Source busy",last_attempt_at=now,
            next_retry_at=retry,
        )
        return {
            "status":"retry_wait",
            "queue_id":row["id"],
            "next_retry_at":_iso(retry),
        }
    except Exception as exc:
        _set_status(
            db,row["id"],status="failed",attempts=attempts,
            last_error=str(exc),last_attempt_at=now,
        )
        return {"status":"failed","queue_id":row["id"],"error":str(exc)}

    stored=0
    for candidate in candidates:
        result=match_external_evidence(db,person["id"],candidate)
        if result.status=="reject":
            continue
        add_external_evidence(
            db,
            person_gedcom_xref=row["person_gedcom_xref"],
            person_name_snapshot=row["person_name_snapshot"],
            source_name=source_name,
            evidence_type=candidate.get("evidence_type","death_notice"),
            source_record_name=candidate.get("source_record_name"),
            event_type=candidate.get("event_type"),
            event_date=candidate.get("event_date"),
            publication=candidate.get("publication"),
            publication_date=candidate.get("publication_date"),
            details=candidate.get("details"),
            birth_date_claim=candidate.get("birth_date_claim"),
            place_claim=candidate.get("place_claim"),
            match_confidence=result.score,
            match_reason="; ".join(result.reasons),
            review_status="new",
        )
        stored+=1

    final="succeeded_with_findings" if stored else "succeeded_no_match"
    _set_status(
        db,row["id"],status=final,attempts=attempts,last_error="",
        last_attempt_at=now,completed_at=now,result_count=stored,
        coverage_scope="national",coverage_completed_at=now,
    )
    return {"status":final,"queue_id":row["id"],"result_count":stored}

def scan_summary(db, source_name=SOURCE_RYERSON):
    rows=queue_rows(db,source_name)
    counts={}
    for row in rows:
        counts[row["status"]]=counts.get(row["status"],0)+1
    return {"source_name":source_name,"total":len(rows),"counts":counts}
