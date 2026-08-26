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


def _surname_form_javascript(surname: str, given_name: str = "") -> str:
    surname_json=json.dumps(surname)
    given_json=json.dumps(given_name or "")
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
  if (gn) gn.value={given_json};
  for (const el of [lo,y1,y2]) if (el) el.value='';
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


def _pagination_control_javascript(target_page: int) -> str:
    """Return JS that clicks Ryerson's in-page pagination control."""
    target_json=json.dumps(str(int(target_page)))
    return f"""
(() => {{
  const target={target_json};
  const controls=[...document.querySelectorAll(
    'a,button,input[type="submit"],input[type="button"]'
  )];

  const textOf=(el) => (
    el.innerText || el.value || el.textContent || ''
  ).trim();

  for (const el of controls) {{
    const text=textOf(el);
    if (text === target) {{
      el.click();
      return JSON.stringify({{
        status:'clicked',
        mode:'page',
        text,
        href:el.href || '',
        onclick:el.getAttribute('onclick') || ''
      }});
    }}
  }}

  for (const el of controls) {{
    const text=textOf(el);
    const aria=(el.getAttribute('aria-label') || '').trim();
    const title=(el.getAttribute('title') || '').trim();
    if (
      /^(next|>|»|›)$/i.test(text) ||
      /next/i.test(aria) ||
      /next/i.test(title)
    ) {{
      el.click();
      return JSON.stringify({{
        status:'clicked',
        mode:'next',
        text,
        href:el.href || '',
        onclick:el.getAttribute('onclick') || ''
      }});
    }}
  }}

  return JSON.stringify({{
    status:'not_found',
    target,
    controls:controls.map(el => ({{
      tag:el.tagName,
      text:textOf(el),
      href:el.href || '',
      onclick:el.getAttribute('onclick') || '',
      name:el.getAttribute('name') || '',
      id:el.id || ''
    }})).filter(x => x.text || x.onclick || x.href.includes('#'))
  }});
}})()
""".strip()


def _click_pagination_control(target_page: int):
    result=_decode(
        _safari_do_javascript(_pagination_control_javascript(target_page)),
        f"pagination control {target_page}",
    )
    if result.get("status")!="clicked":
        raise SourceSearchError(
            f"Ryerson page {target_page} control not found: "
            f"{json.dumps(result.get('controls',[])[:12],ensure_ascii=False)}"
        )
    return result


def _wait_for_distinct_surname_page(
    surname: str,
    previous_keys,
    *,
    timeout_seconds=45.0,
    poll_seconds=1.0,
):
    """Wait until Safari shows surname-correct rows that differ from the prior page."""
    started=time.monotonic()
    last_rows=0
    while time.monotonic()-started<timeout_seconds:
        time.sleep(poll_seconds)
        url,html=_safari_snapshot()
        if _ryerson_page_is_busy(html):
            raise SourceBusyError("Ryerson server overloaded; retry later")
        if not html:
            continue

        rows=parse_ryerson_results(html)
        last_rows=len(rows)
        if not rows or not _rows_correspond_to_surname(rows,surname):
            continue

        keys=_page_record_keys(rows)
        if keys-previous_keys:
            return url,html

    raise SourceSearchError(
        f"Timed out waiting for distinct Ryerson surname page for {surname}; "
        f"last parsed row count={last_rows}"
    )


def _resume_paged_surname(
    surname: str,
    target_page: int,
    *,
    timeout_seconds=45.0,
    poll_seconds=1.0,
):
    """Recreate the first result page, then activate the saved page control."""
    url,html=submit_surname_search(
        surname,
        timeout_seconds=timeout_seconds,
        poll_seconds=poll_seconds,
    )
    if int(target_page)<=1:
        return url,html

    previous_keys=_page_record_keys(parse_ryerson_results(html))
    _click_pagination_control(int(target_page))
    return _wait_for_distinct_surname_page(
        surname,
        previous_keys,
        timeout_seconds=timeout_seconds,
        poll_seconds=poll_seconds,
    )


def _select_forward_pagination_link(links, current_page: int, visited=None):
    """Return the first genuine forward page link, never a completed/backward page."""
    visited=visited or set()
    candidates=[]
    for i,item in enumerate(links,2):
        href=item["href"]
        if href in visited:
            continue
        pn=_page_number_from_link(item["text"],href,i)
        if int(pn) <= int(current_page):
            continue
        candidates.append((int(pn),href))
    if not candidates:
        return None
    candidates.sort(key=lambda x:x[0])
    return candidates[0]


def harvest_surname(
    db,
    surname: str,
    *,
    max_pages=50,
    timeout_seconds=45.0,
    poll_seconds=1.0,
    harvest_kind="surname",
    harvest_value=None,
    progress_key=None,
    enabled_fn=None,
):
    """Harvest one Ryerson search with page identity verification.

    Broad surname searches retain the historical surname identity. Targeted
    surname+given searches may provide their own cache identity and progress key.
    """
    identity_value=harvest_value or surname
    progress_name=progress_key or surname
    if enabled_fn is None:
        enabled_fn=bootstrap_enabled

    def unique_cached_count():
        return db.execute(
            "SELECT COUNT(*) FROM companion_external_notice_cache "
            "WHERE source_name='Ryerson' AND harvest_kind=? "
            "AND lower(trim(harvest_value))=lower(trim(?))",
            (harvest_kind,identity_value),
        ).fetchone()[0]

    progress=surname_progress(db,progress_name)
    pages_completed=int(progress["pages_completed"]) if progress else 0
    rows_total=int(progress["rows_seen"]) if progress else 0
    inserted=int(progress["inserted_rows"]) if progress else 0
    existing=int(progress["existing_rows"]) if progress else 0

    if progress and progress["current_url"] and not progress["is_complete"]:
        page_no=max(1,int(progress["current_page"] or 1))
        current_url=progress["current_url"] or ""
        if current_url.endswith("#") or current_url=="#":
            url,html=_resume_paged_surname(
                surname,
                page_no,
                timeout_seconds=timeout_seconds,
                poll_seconds=poll_seconds,
            )
        else:
            _safari_open(current_url)
            url,html=_wait_for_results(
                expected_surname=surname,
                timeout_seconds=timeout_seconds,
                poll_seconds=poll_seconds,
            )
    else:
        url,html=submit_surname_search(
            surname,
            timeout_seconds=timeout_seconds,
            poll_seconds=poll_seconds,
        )
        page_no=1

    visited=set()
    seen_record_keys=set()
    for row in db.execute(
        "SELECT normalized_json FROM companion_external_notice_cache "
        "WHERE source_name='Ryerson' AND harvest_kind=? "
        "AND lower(trim(harvest_value))=lower(trim(?))",
        (harvest_kind,identity_value),
    ).fetchall():
        try:
            seen_record_keys.add(harvest_record_key(json.loads(row["normalized_json"])))
        except Exception:
            pass

    while pages_completed < max_pages:
        if not enabled_fn(db):
            _save_progress(
                db,progress_name,
                current_page=page_no,current_url=url,pages_completed=pages_completed,
                rows_seen=rows_total,inserted_rows=inserted,existing_rows=existing,
                is_complete=False,
            )
            raise BootstrapPaused(f"Ryerson harvest paused during {surname}")

        if _ryerson_page_is_busy(html):
            _save_progress(
                db,progress_name,
                current_page=page_no,current_url=url,pages_completed=pages_completed,
                rows_seen=rows_total,inserted_rows=inserted,existing_rows=existing,
                is_complete=False,
            )
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
            _save_progress(
                db,progress_name,
                current_page=page_no,current_url=url,pages_completed=pages_completed,
                rows_seen=rows_total,inserted_rows=inserted,existing_rows=existing,
                is_complete=False,
            )
            return {
                "surname":surname,"pages":pages_completed,"rows":rows_total,
                "inserted":inserted,"existing":existing,
                "unique_cached":unique_cached_count(),
                "truncated":True,"paused":False,
                "reason":"next page repeated already-seen Ryerson records",
            }

        cached=cache_harvest_rows(
            db,rows,
            harvest_kind=harvest_kind,
            harvest_value=identity_value,
            harvest_year=0,
            page_number=page_no,
        )
        pages_completed+=1
        rows_total+=len(rows)
        inserted+=cached["inserted"]
        existing+=cached["existing"]
        seen_record_keys.update(page_keys)

        _save_progress(
            db,progress_name,
            current_page=page_no,current_url=url,pages_completed=pages_completed,
            rows_seen=rows_total,inserted_rows=inserted,existing_rows=existing,
            is_complete=False,
        )

        links=pagination_links()
        next_link=_select_forward_pagination_link(
            links,
            page_no,
            visited=visited,
        )

        if next_link is None:
            unique_cached=unique_cached_count()
            _save_progress(
                db,progress_name,
                current_page=page_no,current_url=url,pages_completed=pages_completed,
                rows_seen=rows_total,inserted_rows=inserted,existing_rows=existing,
                is_complete=True,
            )
            return {
                "surname":surname,"pages":pages_completed,"rows":rows_total,
                "inserted":inserted,"existing":existing,"unique_cached":unique_cached,
                "truncated":False,"paused":False,
            }

        next_page,next_url=next_link
        if not enabled_fn(db):
            _save_progress(
                db,progress_name,
                current_page=next_page,current_url=next_url,pages_completed=pages_completed,
                rows_seen=rows_total,inserted_rows=inserted,existing_rows=existing,
                is_complete=False,
            )
            raise BootstrapPaused(f"Ryerson harvest paused during {surname}")

        previous_keys=_page_record_keys(rows)
        if next_url.endswith("#") or next_url=="#":
            _click_pagination_control(next_page)
            url,html=_wait_for_distinct_surname_page(
                surname,
                previous_keys,
                timeout_seconds=timeout_seconds,
                poll_seconds=poll_seconds,
            )
        else:
            _safari_open(next_url)
            url,html=_wait_for_distinct_surname_page(
                surname,
                previous_keys,
                timeout_seconds=timeout_seconds,
                poll_seconds=poll_seconds,
            )
        page_no=next_page

    _save_progress(
        db,progress_name,
        current_page=page_no,current_url=url,pages_completed=pages_completed,
        rows_seen=rows_total,inserted_rows=inserted,existing_rows=existing,
        is_complete=False,
    )
    return {
        "surname":surname,"pages":pages_completed,"rows":rows_total,
        "inserted":inserted,"existing":existing,
        "unique_cached":unique_cached_count(),
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


def _progress_can_finalize_locally(db, surname: str) -> bool:
    """Return True when the saved harvest is internally complete enough to finalise.

    rows_seen counts every parsed row.  inserted_rows counts rows newly cached
    during the harvest, while existing_rows counts rows already present in the
    cache.  Therefore unique cached rows need not equal rows_seen.
    """
    progress=surname_progress(db,surname)
    if not progress:
        return False
    if int(progress["pages_completed"] or 0) <= 0:
        return False
    if int(progress["is_complete"] or 0):
        return True

    cached=_unique_cached_count(db,surname)
    rows_seen=int(progress["rows_seen"] or 0)
    inserted=int(progress["inserted_rows"] or 0)
    existing=int(progress["existing_rows"] or 0)

    return (
        cached>0
        and rows_seen>0
        and inserted+existing==rows_seen
        and cached==inserted
    )


def _finalize_cached_surname(db, queue_row, now):
    surname=queue_row["surname"]
    cached=_unique_cached_count(db,surname)
    progress=surname_progress(db,surname)
    matches=cross_match_surname(db,surname)

    _set_queue(
        db,queue_row["id"],
        status="completed",
        attempts=int(queue_row["attempts"] or 0),
        completed_at=_iso(now),
        result_count=cached,
        match_count=int(matches["findings"]),
        last_error="",
        next_retry_at=None,
    )

    if progress:
        _save_progress(
            db,surname,
            current_page=int(progress["current_page"] or 0),
            current_url=progress["current_url"],
            pages_completed=int(progress["pages_completed"] or 0),
            rows_seen=int(progress["rows_seen"] or 0),
            inserted_rows=int(progress["inserted_rows"] or 0),
            existing_rows=int(progress["existing_rows"] or 0),
            is_complete=True,
        )

    return {
        "status":"completed",
        "surname":surname,
        "result_count":cached,
        "matches":matches,
        "finalized_locally":True,
    }


def ryerson_overload_backoff_seconds(attempts: int) -> int:
    """Short bounded retry schedule for Ryerson's temporary overload page."""
    attempts=max(1,int(attempts))
    schedule=(30,60,120,300)
    return schedule[min(attempts-1,len(schedule)-1)]


def run_one_surname(db, *, now=None, harvest_fn=harvest_surname):
    now=now or _utcnow()
    row=next_surname(db,now)
    if row is None:
        return {"status":"idle"}

    if _progress_can_finalize_locally(db,row["surname"]):
        return _finalize_cached_surname(db,row,now)

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
        retry=now+timedelta(seconds=ryerson_overload_backoff_seconds(attempts))
        _set_queue(
            db,row["id"],
            status="retry_wait",
            attempts=attempts,
            last_error=str(exc),
            next_retry_at=_iso(retry),
        )
        _set_bootstrap_cooldown(db,_iso(retry))
        return {
            "status":"retry_wait",
            "surname":row["surname"],
            "next_retry_at":_iso(retry),
            "source_cooldown":True,
        }
    except SourceSearchError as exc:
        progress=surname_progress(db,row["surname"])
        if progress and not progress["is_complete"] and int(progress["pages_completed"] or 0)>0:
            _set_queue(
                db,row["id"],
                status="queued",
                attempts=attempts,
                result_count=_unique_cached_count(db,row["surname"]),
                last_error=str(exc),
            )
            return {
                "status":"incomplete",
                "surname":row["surname"],
                "error":str(exc),
            }
        if _is_transient_transport_error(str(exc)):
            retry=now+timedelta(seconds=backoff_seconds(attempts))
            _set_queue(
                db,row["id"],
                status="retry_wait",
                attempts=attempts,
                last_error=str(exc),
                next_retry_at=_iso(retry),
            )
            _set_bootstrap_cooldown(db,_iso(retry))
            return {
                "status":"retry_wait",
                "surname":row["surname"],
                "next_retry_at":_iso(retry),
                "source_cooldown":True,
                "error":str(exc),
            }
        _set_queue(
            db,row["id"],
            status="failed",
            attempts=attempts,
            last_error=str(exc),
        )
        return {"status":"failed","surname":row["surname"],"error":str(exc)}
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

    cached_count=int(
        harvest.get("unique_cached",_unique_cached_count(db,row["surname"]))
    )
    progress=surname_progress(db,row["surname"])
    if progress:
        _save_progress(
            db,row["surname"],
            current_page=int(progress["current_page"] or 0),
            current_url=progress["current_url"],
            pages_completed=int(progress["pages_completed"] or 0),
            rows_seen=cached_count,
            inserted_rows=cached_count,
            existing_rows=0,
            is_complete=True,
        )

    matches=cross_match_surname(db,row["surname"])
    _set_queue(
        db,row["id"],
        status="completed",
        attempts=attempts,
        completed_at=_iso(now),
        result_count=cached_count,
        match_count=int(matches["findings"]),
        last_error="",
    )
    _set_bootstrap_cooldown(db,"")
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
META_BOOTSTRAP_COOLDOWN_UNTIL="ryerson_surname_bootstrap_cooldown_until"

def _meta_get(db,key,default=""):
    row=db.execute("SELECT value FROM meta WHERE key=?",(key,)).fetchone()
    return row["value"] if row else default

def _meta_set(db,key,value):
    db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",(key,value))
    db.commit()

def bootstrap_enabled(db):
    return _meta_get(db,META_BOOTSTRAP_ENABLED,"0")=="1"

def bootstrap_cooldown_until(db):
    return _parse_iso(_meta_get(db,META_BOOTSTRAP_COOLDOWN_UNTIL,""))


def _set_bootstrap_cooldown(db,value):
    _meta_set(db,META_BOOTSTRAP_COOLDOWN_UNTIL,value or "")


def bootstrap_source_waiting(db, now=None):
    now=now or _utcnow()
    until=bootstrap_cooldown_until(db)
    return bool(until and until>now)


def _is_transient_transport_error(message: str | None) -> bool:
    low=(message or "").casefold()
    phrases=(
        "submit field not found",
        "surname field not found",
        "search form not recognised",
        "search form not recognized",
        "javascript from apple events",
        "safari automation",
        "timed out waiting for verified ryerson surname results",
        "timed out waiting for ryerson surname results",
    )
    return any(p in low for p in phrases)


def recover_transient_surname_failures(db):
    rows=db.execute(
        "SELECT id,last_error FROM companion_ryerson_surname_queue WHERE status='failed'"
    ).fetchall()
    ids=[r["id"] for r in rows if _is_transient_transport_error(r["last_error"])]
    for qid in ids:
        db.execute(
            "UPDATE companion_ryerson_surname_queue "
            "SET status='queued',attempts=0,last_error=NULL,last_attempt_at=NULL,"
            "next_retry_at=NULL,completed_at=NULL,updated_at=CURRENT_TIMESTAMP "
            "WHERE id=?",
            (qid,),
        )
    db.commit()
    return len(ids)


def reconcile_cached_surnames(db):
    """Complete cached surnames only when no incomplete page checkpoint exists."""
    rows=db.execute(
        """
        SELECT q.id,q.surname,
               COUNT(c.id) cache_count,
               MAX(CASE
                   WHEN p.surname_key IS NOT NULL AND COALESCE(p.is_complete,0)=0
                   THEN 1 ELSE 0
               END) has_incomplete_progress
        FROM companion_ryerson_surname_queue q
        LEFT JOIN companion_external_notice_cache c
          ON c.source_name='Ryerson'
         AND c.harvest_kind='surname'
         AND lower(trim(c.harvest_value))=lower(trim(q.surname))
        LEFT JOIN companion_ryerson_surname_progress p
          ON p.surname_key=q.surname_key
        WHERE q.status IN ('queued','retry_wait','failed')
        GROUP BY q.id,q.surname
        HAVING cache_count>0
        """
    ).fetchall()

    changed=0
    for row in rows:
        if int(row["has_incomplete_progress"] or 0):
            if _progress_can_finalize_locally(db,row["surname"]):
                q=db.execute(
                    "SELECT * FROM companion_ryerson_surname_queue WHERE id=?",
                    (row["id"],),
                ).fetchone()
                _finalize_cached_surname(db,q,_utcnow())
                changed+=1
            continue

        db.execute(
            """
            UPDATE companion_ryerson_surname_queue
            SET status='completed',
                completed_at=COALESCE(completed_at,CURRENT_TIMESTAMP),
                result_count=?,
                last_error='',
                next_retry_at=NULL,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (int(row["cache_count"]),row["id"]),
        )
        changed+=1

    db.commit()
    return changed


def reconcile_cached_surnames_detail(db):
    """Return reconciliation counts for diagnostics."""
    protected=db.execute(
        """
        SELECT COUNT(DISTINCT q.id)
        FROM companion_ryerson_surname_queue q
        JOIN companion_external_notice_cache c
          ON c.source_name='Ryerson'
         AND c.harvest_kind='surname'
         AND lower(trim(c.harvest_value))=lower(trim(q.surname))
        JOIN companion_ryerson_surname_progress p
          ON p.surname_key=q.surname_key
         AND COALESCE(p.is_complete,0)=0
        WHERE q.status IN ('queued','retry_wait','failed')
        """
    ).fetchone()[0]
    changed=reconcile_cached_surnames(db)
    return {
        "reconciled":changed,
        "protected_incomplete":int(protected),
    }



def start_bootstrap(db):
    added=enqueue_unique_surnames(db)
    recovered=recover_transient_surname_failures(db)
    reconciled=reconcile_cached_surnames(db)
    _meta_set(db,META_BOOTSTRAP_ENABLED,"1")
    out=bootstrap_status(db)
    out["newly_queued"]=added
    out["recovered_transient"]=recovered
    out["reconciled_cached"]=reconciled
    return out

def pause_bootstrap(db):
    _meta_set(db,META_BOOTSTRAP_ENABLED,"0")
    return bootstrap_status(db)

def bootstrap_status(db):
    summary=surname_queue_summary(db)
    until=bootstrap_cooldown_until(db)
    return {
        "enabled":bootstrap_enabled(db),
        "total":summary["total"],
        "queued":summary["queued"],
        "retry_wait":summary["retry_wait"],
        "completed":summary["completed"],
        "failed":summary["failed"],
        "source_waiting":bootstrap_source_waiting(db),
        "cooldown_until":until.isoformat() if until else None,
    }

def bootstrap_tick(db, *, now=None, harvest_fn=harvest_surname):
    now=now or _utcnow()
    if not bootstrap_enabled(db):
        return {"status":"paused"}
    if bootstrap_source_waiting(db,now):
        until=bootstrap_cooldown_until(db)
        return {
            "status":"source_wait",
            "next_retry_at":until.isoformat() if until else None,
        }
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
                import traceback
                traceback.print_exc()
                next_allowed=time.monotonic()+interval_seconds
            time.sleep(poll_seconds)
    thread=threading.Thread(target=worker,name="ReunionCompanion-RyersonSurnameBootstrap",daemon=True)
    thread.start()
    return thread
