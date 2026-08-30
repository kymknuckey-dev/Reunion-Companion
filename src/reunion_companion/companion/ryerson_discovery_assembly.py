from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Iterable, Mapping, Any

from .ryerson_discovery_review import remember_discovery


@dataclass(frozen=True)
class AssembledDiscovery:
    person_id: int
    source_name: str
    external_record_key: str
    proposed_fact_key: str
    match_reason: str
    match_confidence: int | None


def _value(row: Mapping[str, Any], *names: str, default=""):
    for name in names:
        try:
            value = row[name]
        except (KeyError, IndexError, TypeError):
            continue
        if value is not None and str(value).strip():
            return value
    return default


def _norm(value) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def _date_key(value) -> str:
    return str(value or "").strip()


def external_record_key(row: Mapping[str, Any]) -> str:
    """Return a stable identity for one Ryerson notice.

    Prefer an upstream/source identifier when available.  Otherwise compose
    identity from fields that describe the published notice itself rather than
    the targeted search that happened to discover it.
    """
    source_id = _value(
        row,
        "external_record_key",
        "source_record_id",
        "notice_id",
        "ryerson_id",
        "record_id",
    )
    if source_id:
        return f"ryerson:{source_id}"

    parts = (
        _norm(_value(row, "surname", "last_name")),
        _norm(_value(row, "given_name", "first_name", "given_names")),
        _date_key(_value(row, "death_date", "event_date")),
        _date_key(_value(row, "publication_date", "published_date")),
        _norm(_value(row, "newspaper", "publication")),
        _norm(_value(row, "notice_type", "type")),
    )
    return "ryerson:" + "|".join(parts)


def proposed_fact_key(row: Mapping[str, Any]) -> str:
    """Describe the useful fact without assuming every candidate changes Reunion."""
    death_date = _date_key(_value(row, "death_date"))
    if death_date:
        return f"death:{death_date}"

    funeral_date = _date_key(_value(row, "funeral_date"))
    if funeral_date:
        return f"funeral:{funeral_date}"

    return ""


_MONTHS = {
    "jan":1,"january":1,"feb":2,"february":2,"mar":3,"march":3,
    "apr":4,"april":4,"may":5,"jun":6,"june":6,"jul":7,"july":7,
    "aug":8,"august":8,"sep":9,"sept":9,"september":9,
    "oct":10,"october":10,"nov":11,"november":11,"dec":12,"december":12,
}

def _definite_date(value):
    text=str(value or '').strip()
    if not text:
        return None
    low=text.casefold()
    if any(token in low for token in ('abt','about','circa','bef','before','aft','after','between','from','to','?')):
        return None
    compact=re.sub(r'\s+','',text).upper()
    m=re.fullmatch(r'(\d{4})-(\d{1,2})-(\d{1,2})',text)
    if m:
        try:
            return date(int(m.group(1)),int(m.group(2)),int(m.group(3)))
        except ValueError:
            return None
    m=re.fullmatch(r'(\d{1,2})([A-Z]{3,9})(\d{4})',compact)
    if m:
        month=_MONTHS.get(m.group(2).casefold())
        if month:
            try:
                return date(int(m.group(3)),month,int(m.group(1)))
            except ValueError:
                return None
    m=re.fullmatch(r'(\d{1,2})[./-](\d{1,2})[./-](\d{4})',text)
    if m:
        try:
            return date(int(m.group(3)),int(m.group(2)),int(m.group(1)))
        except ValueError:
            return None
    return None
def impossible_death_before_birth(row: Mapping[str, Any]) -> bool:
    birth=_definite_date(_value(row,"birth_date","reunion_birth_date","birth_date_claim"))
    event=_definite_date(_value(row,"death_date","funeral_date","event_date"))
    return bool(birth and event and event < birth)

def candidate_is_reviewable(row: Mapping[str, Any]) -> bool:
    """Only assemble rows already associated with one concrete Reunion person."""
    person_id = _value(row, "person_id", "reunion_person_id", default=None)
    if person_id in (None, ""):
        return False

    if impossible_death_before_birth(row):
        return False

    status = _norm(_value(row, "match_status", "status"))
    if status in {"rejected", "excluded", "no_match", "ambiguous"}:
        return False

    confidence = _value(row, "match_confidence", "confidence", default=None)
    if confidence is not None:
        try:
            if float(confidence) < 0:
                return False
        except (TypeError, ValueError):
            pass

    return True


def assemble_candidate(row: Mapping[str, Any]) -> AssembledDiscovery | None:
    if not candidate_is_reviewable(row):
        return None

    person_id = int(_value(row, "person_id", "reunion_person_id"))
    reason = str(
        _value(
            row,
            "match_reason",
            "reason",
            default="Ryerson candidate associated with this Reunion person",
        )
    )

    confidence_raw=_value(row, "match_confidence", "confidence", default=None)
    try:
        confidence=int(float(confidence_raw)) if confidence_raw not in (None, "") else None
    except (TypeError, ValueError):
        confidence=None

    return AssembledDiscovery(
        person_id=person_id,
        source_name="Ryerson",
        external_record_key=external_record_key(row),
        proposed_fact_key=proposed_fact_key(row),
        match_reason=reason,
        match_confidence=confidence,
    )


def assemble_discoveries(db, candidates: Iterable[Mapping[str, Any]]):
    """Persist only currently eligible, chronologically plausible discoveries.

    The review table's unique identity makes this idempotent. Re-running the
    assembler can rediscover a candidate, but remember_discovery() returns the
    existing review record and preserves its state and decision note.

    Ryerson eligibility is enforced here as well as at research-queue creation
    because persisted historical person/notice relationships may outlive the
    Reunion data that originally made a person eligible.
    """
    from .external_evidence_matcher import ryerson_death_candidates

    eligible_person_ids = {
        int(row["person_id"])
        for row in ryerson_death_candidates(db)
    }

    birth_rows = db.execute(
        """
        SELECT person_id,date_text
        FROM events
        WHERE lower(event_type)='birth'
        ORDER BY person_id,id
        """
    ).fetchall()

    birth_dates = {}
    for row in birth_rows:
        pid = int(row["person_id"])
        if pid in birth_dates:
            continue
        parsed = _definite_date(row["date_text"])
        if parsed is not None:
            birth_dates[pid] = parsed

    assembled = []
    skipped = 0

    for candidate in candidates:
        discovery = assemble_candidate(candidate)
        if discovery is None:
            skipped += 1
            continue

        if discovery.person_id not in eligible_person_ids:
            skipped += 1
            continue

        fact = str(discovery.proposed_fact_key or "").strip()
        if ":" in fact:
            kind, raw_date = fact.split(":", 1)
            if kind.casefold() == "death":
                birth_date = birth_dates.get(discovery.person_id)
                death_date = _definite_date(raw_date)
                if (
                    birth_date is not None
                    and death_date is not None
                    and death_date < birth_date
                ):
                    skipped += 1
                    continue

        review = remember_discovery(
            db,
            person_id=discovery.person_id,
            source_name=discovery.source_name,
            external_record_key=discovery.external_record_key,
            proposed_fact_key=discovery.proposed_fact_key,
            match_confidence=discovery.match_confidence,
        )
        assembled.append(
            {
                "discovery": discovery,
                "review": review,
            }
        )

    return {
        "assembled": assembled,
        "assembled_count": len(assembled),
        "skipped_count": skipped,
    }
