"""Browser-assisted Ryerson search and result import.

Direct unattended HTTP access to Ryerson currently receives HTTP 429 from the
user's Mac. This module therefore keeps source interaction in the user's normal
browser while reusing Companion's parser, matcher and persistence layers.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import webbrowser

from .external_evidence import add_external_evidence
from .external_evidence_matcher import match_external_evidence, person_identity_profile
from .ryerson_adapter import (
    DEFAULT_STATE,
    RYERSON_SOURCE,
    build_ryerson_queries,
    parse_ryerson_results,
)

RYERSON_SEARCH_URL = "https://ryersonindex.org/search.php"


@dataclass(frozen=True)
class BrowserSearchPlan:
    url: str
    searches: tuple[dict, ...]


def build_browser_search_plan(profile: dict, state: str = DEFAULT_STATE) -> BrowserSearchPlan:
    searches = tuple(
        {
            "surname": q.surname,
            "given_names": q.given_names,
            "state": q.state,
        }
        for q in build_ryerson_queries(profile, state)
    )
    return BrowserSearchPlan(RYERSON_SEARCH_URL, searches)


def open_ryerson_search(profile: dict, state: str = DEFAULT_STATE, opener=None) -> BrowserSearchPlan:
    plan = build_browser_search_plan(profile, state)
    (opener or webbrowser.open)(plan.url)
    return plan


def _parse_tabular_text(text: str) -> list[dict]:
    rows = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        low = line.casefold()
        if "surname" in low and "given names" in low and "notice type" in low:
            continue

        if "\t" in line:
            cols = [c.strip() for c in line.split("\t")]
        else:
            cols = [c.strip() for c in re.split(r"\s{2,}", line)]

        if len(cols) < 7:
            continue

        cols = cols + [""] * max(0, 9 - len(cols))
        surname, given, notice, date, event, age, details, publication, published = cols[:9]

        if not surname or not given:
            continue

        evidence_type = (
            "funeral_notice"
            if "funeral" in notice.casefold()
            else "death_notice"
            if "death" in notice.casefold()
            else re.sub(r"[^a-z0-9]+", "_", notice.casefold()).strip("_") or "notice"
        )

        birth_claim = None
        m = re.search(r"\bborn\s+(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})", details, re.I)
        if m:
            birth_claim = " ".join(m.group(1).split())

        place_claim = None
        m = re.search(r"\blate of\s+([^()]+?)(?:\s*\(|$)", details, re.I)
        if m:
            place_claim = " ".join(m.group(1).split()).strip(" ,.;")

        row = {
            "evidence_type": evidence_type,
            "source_record_name": f"{given} {surname}".strip(),
            "event_type": event or ("Funeral" if evidence_type == "funeral_notice" else "Death"),
            "event_date": date or None,
            "publication": publication or None,
            "publication_date": published or None,
            "details": details or None,
            "birth_date_claim": birth_claim,
            "place_claim": place_claim,
        }
        if age:
            row["age_claim"] = age
        rows.append(row)
    return rows


def parse_copied_ryerson_content(content: str) -> list[dict]:
    text = content or ""
    if "<table" in text.casefold() or "<tr" in text.casefold():
        rows = parse_ryerson_results(text)
        if rows:
            return rows
    return _parse_tabular_text(text)


def import_copied_ryerson_content(db, pid: int, content: str) -> dict:
    profile = person_identity_profile(db, pid)
    if not profile:
        return {
            "status": "person_not_found",
            "parsed": 0,
            "stored": 0,
            "rejected": 0,
            "findings": (),
        }

    rows = parse_copied_ryerson_content(content)
    stored_ids = []
    rejected = 0
    assessed = []

    for row in rows:
        result = match_external_evidence(db, pid, row)
        assessed.append(
            {
                "source_record_name": row.get("source_record_name"),
                "status": result.status,
                "score": result.score,
                "reasons": result.reasons,
                "contradictions": result.contradictions,
            }
        )
        if result.status == "reject":
            rejected += 1
            continue

        evidence_id = add_external_evidence(
            db,
            person_gedcom_xref=profile["gedcom_xref"],
            person_name_snapshot=profile["display_name"],
            source_name=RYERSON_SOURCE,
            evidence_type=row.get("evidence_type", "death_notice"),
            source_record_name=row.get("source_record_name"),
            event_type=row.get("event_type"),
            event_date=row.get("event_date"),
            publication=row.get("publication"),
            publication_date=row.get("publication_date"),
            details=row.get("details"),
            birth_date_claim=row.get("birth_date_claim"),
            place_claim=row.get("place_claim"),
            match_confidence=result.score,
            match_reason="; ".join(result.reasons),
            review_status="new",
        )
        stored_ids.append(evidence_id)

    return {
        "status": "imported" if stored_ids else "no_accepted_findings",
        "parsed": len(rows),
        "stored": len(stored_ids),
        "rejected": rejected,
        "finding_ids": tuple(stored_ids),
        "findings": tuple(assessed),
    }
