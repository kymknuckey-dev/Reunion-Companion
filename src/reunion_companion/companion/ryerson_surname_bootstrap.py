"""Whole-surname Ryerson bootstrap harvest and location learning.

RC1.0.14.7.2 maintains a persistent queue of unique Reunion surnames. Each
surname is harvested once through Safari, cached locally, cross-matched against
Reunion, and can later be used to learn useful notice locations.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import re
import time

from .external_evidence_scan import SourceBusyError, SourceSearchError, backoff_seconds
from .ryerson_adapter import parse_ryerson_results
from .ryerson_harvest import cache_harvest_rows, cross_match_cached_notices, harvest_record_key
from .ryerson_safari_transport import (
    BrowserTransportUnavailable,
    RYERSON_SEARCH_URL,
    _ryerson_page_is_busy,
    _safari_do_javascript,
    _safari_open,
    _safari_snapshot,
)
from .ryerson_safari_harvest import pagination_links, _page_number_from_link

SOURCE_RYERSON="Ryerson"

class BootstrapPaused(RuntimeError):
    pass



def _utcnow():
    return datetime.now(timezone.utc)


def _iso(dt):
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _parse_iso(value):
    return datetime.fromisoformat(value) if value else None


def _clean_surname(value):
    return " ".join((value or "").split())


def enqueue_unique_surnames(db):
    rows=db.execute(
        """
        SELECT trim(surname) surname,COUNT(*) people_count
        FROM people
        WHERE trim(COALESCE(surname,''))<>''
        GROUP BY lower(trim(surname))
        ORDER BY people_count DESC,lower(trim(surname))
        """
    ).fetchall()
    added=0
    for row in rows:
        surname=_clean_surname(row["surname"])
        if len(surname)<2:
            continue
        cur=db.execute(
            """
            INSERT OR IGNORE INTO companion_ryerson_surname_queue(
                surname,surname_key,people_count,status
            ) VALUES(?,?,?,'queued')
            """,
            (surname,surname.casefold(),int(row["people_count"])),
        )
        added+=int(cur.rowcount or 0)
    db.commit()
    return added


def surname_progress(db, surname: str):
    key=_clean_surname(surname).casefold()
    return db.execute(
        "SELECT * FROM companion_ryerson_surname_progress WHERE surname_key=?",
        (key,),
    ).fetchone()


def _save_progress(
    db,
    surname: str,
    *,
    current_page: int,
    current_url: str | None,
    pages_completed: int,
    rows_seen: int,
    inserted_rows: int,
    existing_rows: int,
    is_complete: bool = False,
):
    key=_clean_surname(surname).casefold()
    db.execute(
        """
        INSERT INTO companion_ryerson_surname_progress(
            surname_key,surname,current_page,current_url,pages_completed,
            rows_seen,inserted_rows,existing_rows,is_complete,updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
        ON CONFLICT(surname_key) DO UPDATE SET
            surname=excluded.surname,
            current_page=excluded.current_page,
            current_url=excluded.current_url,
            pages_completed=excluded.pages_completed,
            rows_seen=excluded.rows_seen,
            inserted_rows=excluded.inserted_rows,
            existing_rows=excluded.existing_rows,
            is_complete=excluded.is_complete,
            updated_at=CURRENT_TIMESTAMP
        """,
        (
            key,surname,int(current_page),current_url,int(pages_completed),
            int(rows_seen),int(inserted_rows),int(existing_rows),
            1 if is_complete else 0,
        ),
    )
    db.commit()


def _clear_progress(db, surname: str):
    db.execute(
        "DELETE FROM companion_ryerson_surname_progress WHERE surname_key=?",
        (_clean_surname(surname).casefold(),),
    )
    db.commit()


def surname_queue_rows(db):
    return db.execute(
        """
        SELECT * FROM companion_ryerson_surname_queue
        ORDER BY
          CASE status
            WHEN 'retry_wait' THEN 0
            WHEN 'queued' THEN 1
            WHEN 'searching' THEN 2
            WHEN 'completed' THEN 3
            ELSE 4
          END,
          people_count DESC,surname_key
        """
    ).fetchall()


def surname_queue_summary(db):
    rows=surname_queue_rows(db)
    counts={}
    for row in rows:
        counts[row["status"]]=counts.get(row["status"],0)+1
    return {
        "total":len(rows),
        "counts":counts,
        "queued":counts.get("queued",0),
        "retry_wait":counts.get("retry_wait",0),
        "completed":counts.get("completed",0),
        "failed":counts.get("failed",0),
    }


def next_surname(db, now=None):
    now=now or _utcnow()
    rows=db.execute(
        """
        SELECT * FROM companion_ryerson_surname_queue
        WHERE status IN ('queued','retry_wait')
        ORDER BY
          CASE status WHEN 'retry_wait' THEN 0 ELSE 1 END,
          people_count DESC,surname_key
        """
    ).fetchall()
    for row in rows:
        if row["status"]=="queued":
            return row
        due=_parse_iso(row["next_retry_at"])
        if due is None or due<=now:
            return row
    return None


def _set_queue(db, qid, **values):
    fields=["updated_at=CURRENT_TIMESTAMP"]
    args=[]
    for key,value in values.items():
        fields.append(f"{key}=?")
        args.append(value)
    args.append(qid)
    db.execute(
        f"UPDATE companion_ryerson_surname_queue SET {','.join(fields)} WHERE id=?",
        tuple(args),
    )
    db.commit()


def _surname_form_javascript(surname: str) -> str:
    surname_json=json.dumps(surname)
    return f"""
(() => {{
  const sn=document.querySelector('[name="search_sn"]');
  const gn=document.querySelector('[name="search_gn"]');
  const lo=document.querySelector('[name="search_lo"]');
  const y1=document.querySelector('[name="search_y1"]');
  const y2=document.querySelector('[name="search_y2"]');
  const submit=document.querySelector('[name="search"][type="submit"]');
  if (!sn) return JSON.stringify({{status:'form_not_recognised',reason:'surname field not found'}});
  if (!submit) return JSON.stringify({{status:'form_not_recognised',reason:'submit field not found'}});

  sn.value={surname_json};
  for (const el of [gn,lo,y1,y2]) if (el) el.value='';
  for (const el of [sn,gn,lo,y1,y2]) if (el) {{
    el.dispatchEvent(new Event('input',{{bubbles:true}}));
    el.dispatchEvent(new Event('change',{{bubbles:true}}));
  }}
  submit.click();
  return JSON.stringify({{status:'submitted'}});
}})()
""".strip()


def _decode(raw,label):
    try:
        return json.loads(raw)
    except Exception as exc:
        raise SourceSearchError(f"Could not decode Safari {label}: {raw[:200]}") from exc


def _result_surname(name: str | None) -> str:
    text=" ".join((name or "").split())
    if not text:
        return ""
    tokens=re.findall(r"[A-Za-z][A-Za-z'’-]*",text)
    return tokens[-1].casefold() if tokens else ""


def _rows_correspond_to_surname(rows, surname: str) -> bool:
    expected=_clean_surname(surname).casefold()
    if not expected or not rows:
        return False
    observed=[_result_surname(r.get("source_record_name")) for r in rows]
    observed=[x for x in observed if x]
    if not observed:
        return False
    matching=sum(1 for x in observed if x==expected)
    return matching / len(observed) >= 0.90


def _page_record_keys(rows):
    return {harvest_record_key(r) for r in rows}


def _unique_cached_count(db, surname: str) -> int:
    return int(db.execute(
        """
        SELECT COUNT(*)
        FROM companion_external_notice_cache
        WHERE source_name='Ryerson'
          AND harvest_kind='surname'
          AND lower(trim(harvest_value))=lower(trim(?))
        """,
        (surname,),
    ).fetchone()[0])


def _wait_for_results(*, expected_surname=None, timeout_seconds=45.0, poll_seconds=1.0):
    started=time.monotonic()
    last_rows=0
    while time.monotonic()-started<timeout_seconds:
        time.sleep(poll_seconds)
        url,html=_safari_snapshot()
        if _ryerson_page_is_busy(html):
            raise SourceBusyError("Ryerson server overloaded; retry later")
        if not html:
            continue
        if expected_surname is None:
            if "<table" in html.casefold() or "ryerson" in html.casefold():
                return url,html
            continue

        rows=parse_ryerson_results(html)
        last_rows=len(rows)
        if _rows_correspond_to_surname(rows,expected_surname):
            return url,html

    label=f" for {expected_surname}" if expected_surname else ""
    raise SourceSearchError(
        f"Timed out waiting for verified Ryerson surname results{label}; "
        f"last parsed row count={last_rows}"
    )


def submit_surname_search(surname: str, *, timeout_seconds=45.0, poll_seconds=1.0):
    _safari_open(RYERSON_SEARCH_URL)
    _wait_for_results(timeout_seconds=timeout_seconds,poll_seconds=poll_seconds)
    result=_decode(_safari_do_javascript(_surname_form_javascript(surname)),"surname submission")
    if result.get("status")!="submitted":
        raise BrowserTransportUnavailable(result.get("reason") or "Surname search form not recognised")
    return _wait_for_results(
        expected_surname=surname,
        timeout_seconds=timeout_seconds,
        poll_seconds=poll_seconds,
    )


def harvest_surname(db, surname: str, *, max_pages=50, timeout_seconds=45.0, poll_seconds=1.0):
    """Harvest one surname with page identity verification."""
    progress=surname_progress(db,surname)
    pages_completed=int(progress["pages_completed"]) if progress else 0
    rows_total=int(progress["rows_seen"]) if progress else 0
    inserted=int(progress["inserted_rows"]) if progress else 0
    existing=int(progress["existing_rows"]) if progress else 0

    if progress and progress["current_url"] and not progress["is_complete"]:
        _safari_open(progress["current_url"])
        url,html=_wait_for_results(expected_surname=surname,timeout_seconds=timeout_seconds,poll_seconds=poll_seconds)
        page_no=max(1,int(progress["current_page"] or 1))
    else:
        url,html=submit_surname_search(surname,timeout_seconds=timeout_seconds,poll_seconds=poll_seconds)
        page_no=1

    visited=set()
    seen_record_keys=set()
    for row in db.execute(
        "SELECT normalized_json FROM companion_external_notice_cache "
        "WHERE source_name='Ryerson' AND harvest_kind='surname' "
        "AND lower(trim(harvest_value))=lower(trim(?))",
        (surname,),
    ).fetchall():
        try:
            seen_record_keys.add(harvest_record_key(json.loads(row["normalized_json"])))
        except Exception:
            pass

    while pages_completed < max_pages:
        if not bootstrap_enabled(db):
            _save_progress(db,surname,current_page=page_no,current_url=url,pages_completed=pages_completed,
                           rows_seen=rows_total,inserted_rows=inserted,existing_rows=existing,is_complete=False)
            raise BootstrapPaused(f"Surname bootstrap paused during {surname}")

        if _ryerson_page_is_busy(html):
            _save_progress(db,surname,current_page=page_no,current_url=url,pages_completed=pages_completed,
                           rows_seen=rows_total,inserted_rows=inserted,existing_rows=existing,is_complete=False)
            raise SourceBusyError("Ryerson server overloaded; retry later")

        if url in visited:
            raise SourceSearchError(f"Pagination loop detected during {surname}")
        visited.add(url)

        rows=parse_ryerson_results(html)
        if rows and not _rows_correspond_to_surname(rows,surname):
            raise SourceSearchError(f"Unverified surname result page for {surname}")

        page_keys=_page_record_keys(rows)
        new_keys=page_keys-seen_record_keys
        if page_no > 1 and rows and not new_keys:
            _save_progress(db,surname,current_page=page_no,current_url=url,pages_completed=pages_completed,
                           rows_seen=rows_total,inserted_rows=inserted,existing_rows=existing,is_complete=False)
            return {
                "surname":surname,"pages":pages_completed,"rows":rows_total,
                "inserted":inserted,"existing":existing,
                "unique_cached":_unique_cached_count(db,surname),
                "truncated":True,"paused":False,
                "reason":"next page repeated already-seen Ryerson records",
            }

        cached=cache_harvest_rows(db,rows,harvest_kind="surname",harvest_value=surname,harvest_year=0,page_number=page_no)
        pages_completed+=1
        rows_total+=len(rows)
        inserted+=cached["inserted"]
        existing+=cached["existing"]
        seen_record_keys.update(page_keys)

        _save_progress(db,surname,current_page=page_no,current_url=url,pages_completed=pages_completed,
                       rows_seen=rows_total,inserted_rows=inserted,existing_rows=existing,is_complete=False)

        links=pagination_links()
        next_link=None
        for i,item in enumerate(links,2):
            href=item["href"]
            if href in visited:
                continue
            next_link=(_page_number_from_link(item["text"],href,i),href)
            break

        if next_link is None:
            unique_cached=_unique_cached_count(db,surname)
            _save_progress(db,surname,current_page=page_no,current_url=url,pages_completed=pages_completed,
                           rows_seen=rows_total,inserted_rows=inserted,existing_rows=existing,is_complete=True)
            return {
                "surname":surname,"pages":pages_completed,"rows":rows_total,
                "inserted":inserted,"existing":existing,"unique_cached":unique_cached,
                "truncated":False,"paused":False,
            }

        next_page,next_url=next_link
        if not bootstrap_enabled(db):
            _save_progress(db,surname,current_page=next_page,current_url=next_url,pages_completed=pages_completed,
                           rows_seen=rows_total,inserted_rows=inserted,existing_rows=existing,is_complete=False)
            raise BootstrapPaused(f"Surname bootstrap paused during {surname}")

        _safari_open(next_url)
        url,html=_wait_for_results(expected_surname=surname,timeout_seconds=timeout_seconds,poll_seconds=poll_seconds)
        page_no=next_page

    _save_progress(db,surname,current_page=page_no,current_url=url,pages_completed=pages_completed,
                   rows_seen=rows_total,inserted_rows=inserted,existing_rows=existing,is_complete=False)
    return {
        "surname":surname,"pages":pages_completed,"rows":rows_total,
        "inserted":inserted,"existing":existing,
        "unique_cached":_unique_cached_count(db,surname),
        "truncated":True,"paused":False,
        "reason":"maximum page safety limit reached",
    }


def cross_match_surname(db, surname: str, *, minimum_score=55):
    return cross_match_cached_notices(
        db,
        harvest_kind="surname",
        harvest_value=surname,
        minimum_score=minimum_score,
    )


def run_one_surname(db, *, now=None, harvest_fn=harvest_surname):
    now=now or _utcnow()
    row=next_surname(db,now)
    if row is None:
        return {"status":"idle"}

    attempts=int(row["attempts"] or 0)+1
    _set_queue(
        db,row["id"],
        status="searching",
        attempts=attempts,
        last_attempt_at=_iso(now),
        last_error="",
        next_retry_at=None,
    )

    try:
        harvest=harvest_fn(db,row["surname"])
    except BootstrapPaused:
        _set_queue(
            db,row["id"],
            status="queued",
            attempts=attempts,
            last_error="Paused during paged surname harvest",
        )
        return {"status":"paused","surname":row["surname"]}
    except SourceBusyError as exc:
        retry=now+timedelta(seconds=backoff_seconds(attempts))
        _set_queue(
            db,row["id"],
            status="retry_wait",
            attempts=attempts,
            last_error=str(exc),
            next_retry_at=_iso(retry),
        )
        return {
            "status":"retry_wait",
            "surname":row["surname"],
            "next_retry_at":_iso(retry),
        }
    except Exception as exc:
        _set_queue(
            db,row["id"],
            status="failed",
            attempts=attempts,
            last_error=str(exc),
        )
        return {"status":"failed","surname":row["surname"],"error":str(exc)}

    if harvest.get("truncated"):
        _set_queue(
            db,row["id"],
            status="queued",
            attempts=attempts,
            result_count=int(harvest.get("unique_cached",_unique_cached_count(db,row["surname"]))),
            last_error=harvest.get("reason") or "Paged surname harvest incomplete; resume required",
        )
        return {
            "status":"incomplete",
            "surname":row["surname"],
            "harvest":harvest,
        }

    matches=cross_match_surname(db,row["surname"])
    _set_queue(
        db,row["id"],
        status="completed",
        attempts=attempts,
        completed_at=_iso(now),
        result_count=int(harvest.get("unique_cached",_unique_cached_count(db,row["surname"]))),
        match_count=int(matches["findings"]),
        last_error="",
    )
    _clear_progress(db,row["surname"])
    return {
        "status":"completed",
        "surname":row["surname"],
        "harvest":harvest,
        "matches":matches,
    }


def location_learning(db, *, minimum_confidence=55, limit=100):
    """Summarise location phrases among reviewable Ryerson findings."""
    rows=db.execute(
        """
        SELECT COALESCE(place_claim,'') place_claim,COUNT(*) count
        FROM companion_external_evidence
        WHERE source_name='Ryerson'
          AND COALESCE(match_confidence,0)>=?
          AND trim(COALESCE(place_claim,''))<>''
        GROUP BY lower(trim(place_claim))
        ORDER BY count DESC,place_claim
        LIMIT ?
        """,
        (int(minimum_confidence),int(limit)),
    ).fetchall()
    return [{"location":r["place_claim"],"count":r["count"]} for r in rows]


META_BOOTSTRAP_ENABLED="ryerson_surname_bootstrap_enabled"

def _meta_get(db,key,default=""):
    row=db.execute("SELECT value FROM meta WHERE key=?",(key,)).fetchone()
    return row["value"] if row else default

def _meta_set(db,key,value):
    db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",(key,value))
    db.commit()

def bootstrap_enabled(db):
    return _meta_get(db,META_BOOTSTRAP_ENABLED,"0")=="1"

def reconcile_cached_surnames(db):
    rows=db.execute(
        "SELECT q.id,q.surname,COUNT(c.id) cache_count "
        "FROM companion_ryerson_surname_queue q "
        "LEFT JOIN companion_external_notice_cache c "
        "ON c.source_name='Ryerson' AND c.harvest_kind='surname' "
        "AND lower(trim(c.harvest_value))=lower(trim(q.surname)) "
        "WHERE q.status IN ('queued','retry_wait','failed') "
        "GROUP BY q.id,q.surname HAVING cache_count>0"
    ).fetchall()
    changed=0
    for row in rows:
        db.execute(
            "UPDATE companion_ryerson_surname_queue "
            "SET status='completed', completed_at=COALESCE(completed_at,CURRENT_TIMESTAMP), "
            "result_count=?, last_error='', next_retry_at=NULL, updated_at=CURRENT_TIMESTAMP "
            "WHERE id=?",
            (int(row['cache_count']),row['id']),
        )
        changed+=1
    db.commit()
    return changed

def start_bootstrap(db):
    added=enqueue_unique_surnames(db)
    reconciled=reconcile_cached_surnames(db)
    _meta_set(db,META_BOOTSTRAP_ENABLED,"1")
    out=bootstrap_status(db)
    out["newly_queued"]=added
    out["reconciled_cached"]=reconciled
    return out

def pause_bootstrap(db):
    _meta_set(db,META_BOOTSTRAP_ENABLED,"0")
    return bootstrap_status(db)

def bootstrap_status(db):
    summary=surname_queue_summary(db)
    return {
        "enabled":bootstrap_enabled(db),
        "total":summary["total"],
        "queued":summary["queued"],
        "retry_wait":summary["retry_wait"],
        "completed":summary["completed"],
        "failed":summary["failed"],
    }

def bootstrap_tick(db, *, now=None, harvest_fn=harvest_surname):
    if not bootstrap_enabled(db):
        return {"status":"paused"}
    return run_one_surname(db,now=now,harvest_fn=harvest_fn)

def start_background_surname_bootstrap(db_path, *, interval_seconds=120, poll_seconds=10):
    import threading
    def worker():
        next_allowed=0.0
        while True:
            try:
                from .database import connect
                db=connect(db_path)
                try:
                    enabled=bootstrap_enabled(db)
                finally:
                    db.close()
                now_mono=time.monotonic()
                if enabled and now_mono>=next_allowed:
                    db=connect(db_path)
                    try:
                        bootstrap_tick(db)
                    finally:
                        db.close()
                    next_allowed=time.monotonic()+interval_seconds
            except Exception:
                next_allowed=time.monotonic()+interval_seconds
            time.sleep(poll_seconds)
    thread=threading.Thread(target=worker,name="ReunionCompanion-RyersonSurnameBootstrap",daemon=True)
    thread.start()
    return thread
