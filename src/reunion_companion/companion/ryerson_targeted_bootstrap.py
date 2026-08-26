"""Hybrid targeted Ryerson bootstrap queue."""

from __future__ import annotations

import re

META_TARGETED_ENABLED="ryerson_targeted_bootstrap_enabled"
META_CORE_SURNAMES="ryerson_targeted_core_surnames"
OLD_SURNAME_ENABLED="ryerson_surname_bootstrap_enabled"

PLACEHOLDER_NAME_KEYS={"", "?", "-", "unknown", "unnamed", "un-named", "not known", "notknown", "nknown", "n/n", "nn"}


def _is_placeholder_name(value):
    return _key_part(value) in PLACEHOLDER_NAME_KEYS


SCHEMA="""
CREATE TABLE IF NOT EXISTS companion_ryerson_targeted_queue(
    id INTEGER PRIMARY KEY,
    search_kind TEXT NOT NULL,
    surname TEXT NOT NULL,
    given_name TEXT NOT NULL DEFAULT '',
    search_key TEXT NOT NULL UNIQUE,
    people_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'queued',
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    last_attempt_at TEXT,
    next_retry_at TEXT,
    completed_at TEXT,
    result_count INTEGER NOT NULL DEFAULT 0,
    match_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_companion_ryerson_targeted_queue_status
ON companion_ryerson_targeted_queue(status,next_retry_at,people_count);
"""

def ensure_targeted_schema(db):
    db.executescript(SCHEMA)
    db.commit()

def _meta_get(db,key,default=""):
    row=db.execute("SELECT value FROM meta WHERE key=?",(key,)).fetchone()
    return row["value"] if row else default

def _meta_set(db,key,value):
    db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",(key,value))
    db.commit()

def _clean(value):
    return " ".join((value or "").split()).strip()

def _key_part(value):
    return re.sub(r"\s+"," ",_clean(value).casefold())

def first_given_name(given_names):
    text=_clean(given_names)
    return text.split()[0] if text else ""

def search_key(search_kind,surname,given_name=""):
    kind=_key_part(search_kind)
    surname_key=_key_part(surname)
    given_key=_key_part(given_name)
    return f"surname:{surname_key}" if kind=="surname" else f"name:{surname_key}|{given_key}"

def configured_core_surnames(db):
    raw=_meta_get(db,META_CORE_SURNAMES,"Knuckey")
    out=[]
    seen=set()
    for part in raw.split(","):
        clean=_clean(part)
        key=clean.casefold()
        if clean and key not in seen:
            seen.add(key)
            out.append(clean)
    return out

def set_core_surnames(db,surnames):
    out=[]
    seen=set()
    for surname in surnames:
        clean=_clean(surname)
        key=clean.casefold()
        if clean and key not in seen:
            seen.add(key)
            out.append(clean)
    _meta_set(db,META_CORE_SURNAMES,", ".join(out))
    return out

def _people_rows(db):
    return db.execute(
        "SELECT surname,given_names FROM people "
        "WHERE trim(COALESCE(surname,''))<>''"
    ).fetchall()

def desired_searches(db):
    core={x.casefold() for x in configured_core_surnames(db)}
    grouped={}
    for row in _people_rows(db):
        surname=_clean(row["surname"])
        if not surname or _is_placeholder_name(surname):
            continue
        if surname.casefold() in core:
            kind="surname"
            given=""
        else:
            given=first_given_name(row["given_names"])
            if not given or _is_placeholder_name(given):
                continue
            kind="name"
        key=search_key(kind,surname,given)
        item=grouped.setdefault(key,{
            "search_kind":kind,
            "surname":surname,
            "given_name":given,
            "search_key":key,
            "people_count":0,
        })
        item["people_count"]+=1
    return sorted(
        grouped.values(),
        key=lambda x:(-x["people_count"],x["surname"].casefold(),x["given_name"].casefold()),
    )

def populate_targeted_queue(db):
    ensure_targeted_schema(db)
    desired=desired_searches(db)
    added=0
    updated=0
    for item in desired:
        existing=db.execute(
            "SELECT id,people_count FROM companion_ryerson_targeted_queue WHERE search_key=?",
            (item["search_key"],),
        ).fetchone()
        if existing:
            if int(existing["people_count"] or 0)!=int(item["people_count"]):
                db.execute(
                    "UPDATE companion_ryerson_targeted_queue "
                    "SET people_count=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (int(item["people_count"]),existing["id"]),
                )
                updated+=1
            continue
        db.execute(
            "INSERT INTO companion_ryerson_targeted_queue("
            "search_kind,surname,given_name,search_key,people_count,status"
            ") VALUES(?,?,?,?,?,'queued')",
            (
                item["search_kind"],item["surname"],item["given_name"],
                item["search_key"],int(item["people_count"]),
            ),
        )
        added+=1
    db.commit()
    return {"desired":len(desired),"added":added,"updated":updated}

def targeted_status(db):
    ensure_targeted_schema(db)
    rows=db.execute(
        "SELECT status,COUNT(*) n FROM companion_ryerson_targeted_queue GROUP BY status"
    ).fetchall()
    counts={r["status"]:int(r["n"]) for r in rows}
    return {
        "enabled":_meta_get(db,META_TARGETED_ENABLED,"0")=="1",
        "total":sum(counts.values()),
        "queued":counts.get("queued",0),
        "retry_wait":counts.get("retry_wait",0),
        "searching":counts.get("searching",0),
        "completed":counts.get("completed",0),
        "failed":counts.get("failed",0),
        "core_surnames":configured_core_surnames(db),
    }

def start_targeted_bootstrap(db):
    ensure_targeted_schema(db)
    _meta_set(db,OLD_SURNAME_ENABLED,"0")
    population=populate_targeted_queue(db)
    _meta_set(db,META_TARGETED_ENABLED,"1")
    out=targeted_status(db)
    out.update(population)
    return out

def pause_targeted_bootstrap(db):
    _meta_set(db,META_TARGETED_ENABLED,"0")
    return targeted_status(db)

def targeted_enabled(db):
    return _meta_get(db,META_TARGETED_ENABLED,"0")=="1"

def cache_identity_for_search(row):
    if row["search_kind"]=="surname":
        return {"harvest_kind":"surname","harvest_value":_clean(row["surname"])}
    return {
        "harvest_kind":"surname_given",
        "harvest_value":f'{_clean(row["surname"])}|{_clean(row["given_name"])}',
    }



import json
import time
from datetime import datetime, timedelta, timezone

from .external_evidence_scan import SourceBusyError, SourceSearchError

META_TARGETED_COOLDOWN_UNTIL="ryerson_targeted_bootstrap_cooldown_until"


def _utcnow():
    return datetime.now(timezone.utc)


def _iso(value):
    return value.isoformat() if value else None


def _parse_iso(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def targeted_form_javascript(surname: str, given_name: str="") -> str:
    sn=json.dumps(_clean(surname))
    gn=json.dumps(_clean(given_name))
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
  sn.value={sn};
  if (gn) gn.value={gn};
  for (const el of [lo,y1,y2]) if (el) el.value='';
  submit.click();
  return JSON.stringify({{status:'submitted',surname:sn.value,given_name:gn?gn.value:''}});
}})()
"""


def _targeted_cooldown_until(db):
    return _parse_iso(_meta_get(db,META_TARGETED_COOLDOWN_UNTIL,""))


def _set_targeted_cooldown(db,value):
    _meta_set(db,META_TARGETED_COOLDOWN_UNTIL,value or "")


def targeted_source_waiting(db, now=None):
    now=now or _utcnow()
    until=_targeted_cooldown_until(db)
    return bool(until and until>now)


def targeted_overload_backoff_seconds(attempts: int) -> int:
    attempts=max(1,int(attempts))
    schedule=(30,60,120,300)
    return schedule[min(attempts-1,len(schedule)-1)]


def next_targeted_search(db, now=None):
    ensure_targeted_schema(db)
    now=now or _utcnow()
    rows=db.execute(
        """
        SELECT *
        FROM companion_ryerson_targeted_queue
        WHERE status IN ('queued','retry_wait')
        ORDER BY
          CASE status WHEN 'retry_wait' THEN 0 ELSE 1 END,
          people_count DESC,
          lower(surname),
          lower(given_name)
        """
    ).fetchall()
    for row in rows:
        if row["status"]=="queued":
            return row
        due=_parse_iso(row["next_retry_at"])
        if due is None or due<=now:
            return row
    return None


def _set_targeted_queue(db, qid, **values):
    fields=["updated_at=CURRENT_TIMESTAMP"]
    args=[]
    for key,value in values.items():
        fields.append(f"{key}=?")
        args.append(value)
    args.append(qid)
    db.execute(
        f"UPDATE companion_ryerson_targeted_queue SET {','.join(fields)} WHERE id=?",
        tuple(args),
    )
    db.commit()


def targeted_search_descriptor(row):
    return {
        "search_kind":row["search_kind"],
        "surname":row["surname"],
        "given_name":row["given_name"],
        "search_key":row["search_key"],
        **cache_identity_for_search(row),
    }


def run_one_targeted(db, *, now=None, search_fn):
    now=now or _utcnow()

    if not targeted_enabled(db):
        return {"status":"paused"}

    if targeted_source_waiting(db,now):
        until=_targeted_cooldown_until(db)
        return {"status":"source_wait","next_retry_at":_iso(until)}

    row=next_targeted_search(db,now)
    if row is None:
        return {"status":"idle"}

    attempts=int(row["attempts"] or 0)+1
    _set_targeted_queue(
        db,row["id"],
        status="searching",
        attempts=attempts,
        last_attempt_at=_iso(now),
        last_error="",
        next_retry_at=None,
    )

    try:
        result=search_fn(db,targeted_search_descriptor(row))
    except SourceBusyError as exc:
        retry=now+timedelta(seconds=targeted_overload_backoff_seconds(attempts))
        _set_targeted_queue(
            db,row["id"],
            status="retry_wait",
            attempts=attempts,
            last_error=str(exc),
            next_retry_at=_iso(retry),
        )
        _set_targeted_cooldown(db,_iso(retry))
        return {
            "status":"retry_wait",
            "search_key":row["search_key"],
            "next_retry_at":_iso(retry),
            "source_cooldown":True,
        }
    except SourceSearchError as exc:
        retry=now+timedelta(seconds=targeted_overload_backoff_seconds(attempts))
        _set_targeted_queue(
            db,row["id"],
            status="retry_wait",
            attempts=attempts,
            last_error=str(exc),
            next_retry_at=_iso(retry),
        )
        return {
            "status":"retry_wait",
            "search_key":row["search_key"],
            "next_retry_at":_iso(retry),
            "error":str(exc),
        }
    except Exception as exc:
        _set_targeted_queue(
            db,row["id"],
            status="failed",
            attempts=attempts,
            last_error=f"{type(exc).__name__}: {exc}",
        )
        return {
            "status":"failed",
            "search_key":row["search_key"],
            "error":f"{type(exc).__name__}: {exc}",
        }

    result=result or {}
    _set_targeted_queue(
        db,row["id"],
        status="completed",
        attempts=attempts,
        completed_at=_iso(now),
        result_count=int(result.get("result_count",0)),
        match_count=int(result.get("match_count",0)),
        last_error="",
        next_retry_at=None,
    )
    _set_targeted_cooldown(db,"")
    return {
        "status":"completed",
        "search_key":row["search_key"],
        "result_count":int(result.get("result_count",0)),
        "match_count":int(result.get("match_count",0)),
    }


def targeted_tick(db, *, now=None, search_fn):
    return run_one_targeted(db,now=now,search_fn=search_fn)


def start_background_targeted_bootstrap(
    db_path, *, search_fn, interval_seconds=120, poll_seconds=10
):
    import threading

    def worker():
        next_allowed=0.0
        while True:
            try:
                from .database import connect
                db=connect(db_path)
                try:
                    enabled=targeted_enabled(db)
                    waiting=targeted_source_waiting(db)
                finally:
                    db.close()

                now_mono=time.monotonic()
                if enabled and not waiting and now_mono>=next_allowed:
                    db=connect(db_path)
                    try:
                        targeted_tick(db,search_fn=search_fn)
                    finally:
                        db.close()
                    next_allowed=time.monotonic()+interval_seconds
            except Exception:
                import traceback
                traceback.print_exc()
                next_allowed=time.monotonic()+interval_seconds
            time.sleep(poll_seconds)

    thread=threading.Thread(
        target=worker,
        name="ReunionCompanion-RyersonTargetedBootstrap",
        daemon=True,
    )
    thread.start()
    return thread


def live_targeted_search(db, descriptor):
    """Run one targeted search through the verified Safari harvester."""
    from . import ryerson_surname_bootstrap as broad
    from .external_evidence_matcher import cross_match_cached_notices

    surname=_clean(descriptor["surname"])
    given=_clean(descriptor.get("given_name") or "")
    identity=cache_identity_for_search(descriptor)

    original_form=broad._surname_form_javascript
    if given:
        def targeted_form(search_surname):
            return original_form(search_surname,given)
        broad._surname_form_javascript=targeted_form

    try:
        result=broad.harvest_surname(
            db,
            surname,
            harvest_kind=identity["harvest_kind"],
            harvest_value=identity["harvest_value"],
            progress_key=descriptor["search_key"],
            enabled_fn=lambda _db: True,
        )
    finally:
        broad._surname_form_javascript=original_form

    matches=cross_match_cached_notices(
        db,
        harvest_kind=identity["harvest_kind"],
        harvest_value=identity["harvest_value"],
        minimum_score=55,
    )
    return {
        "result_count":int(result.get("unique_cached",0)),
        "match_count":int(matches.get("findings",0)),
        "harvest":result,
        "matches":matches,
        "cache_identity":identity,
    }


def run_selected_targeted_search(db, search_key_value: str):
    """Run exactly one targeted queue item for deliberate live QA."""
    ensure_targeted_schema(db)
    row=db.execute(
        "SELECT * FROM companion_ryerson_targeted_queue WHERE search_key=?",
        (search_key_value,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Targeted Ryerson search not found: {search_key_value}")
    return live_targeted_search(db,targeted_search_descriptor(row))
