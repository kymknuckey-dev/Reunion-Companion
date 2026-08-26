"""Ryerson annual-harvest cache and local cross-match foundation."""

from __future__ import annotations

import hashlib
import json
import re

from .external_evidence import add_external_evidence
from .external_evidence_matcher import death_research_state, match_external_evidence

RYERSON_SOURCE = "Ryerson"


def _norm(value: str | None) -> str:
    value=(value or "").casefold()
    value=re.sub(r"[^a-z0-9]+"," ",value)
    return " ".join(value.split())


def harvest_record_key(row: dict) -> str:
    fields=(
        row.get("evidence_type"),
        row.get("source_record_name"),
        row.get("event_type"),
        row.get("event_date"),
        row.get("publication"),
        row.get("publication_date"),
        row.get("details"),
        row.get("birth_date_claim"),
        row.get("place_claim"),
    )
    raw="\x1f".join(_norm(x) for x in fields)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def cache_harvest_rows(db, rows, *, harvest_kind: str, harvest_value: str,
                       harvest_year: int, page_number: int = 1):
    inserted=0
    existing=0
    ids=[]
    for row in rows:
        key=harvest_record_key(row)
        cur=db.execute(
            """
            INSERT OR IGNORE INTO companion_external_notice_cache(
                source_name,record_key,harvest_kind,harvest_value,harvest_year,
                page_number,evidence_type,source_record_name,event_type,event_date,
                publication,publication_date,details,birth_date_claim,place_claim,
                normalized_json
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                RYERSON_SOURCE,key,harvest_kind,harvest_value,int(harvest_year),
                int(page_number),row.get("evidence_type"),row.get("source_record_name"),
                row.get("event_type"),row.get("event_date"),row.get("publication"),
                row.get("publication_date"),row.get("details"),
                row.get("birth_date_claim"),row.get("place_claim"),
                json.dumps(row,sort_keys=True,ensure_ascii=False),
            ),
        )
        inserted += int(bool(cur.rowcount))
        existing += int(not bool(cur.rowcount))
        found=db.execute(
            "SELECT id FROM companion_external_notice_cache WHERE source_name=? AND record_key=?",
            (RYERSON_SOURCE,key),
        ).fetchone()
        ids.append(found["id"])
    db.commit()
    return {"inserted":inserted,"existing":existing,"notice_ids":ids}


def cached_notices(db, *, year: int | None = None, harvest_kind: str | None = None,
                   harvest_value: str | None = None):
    where=["source_name=?"]
    args=[RYERSON_SOURCE]
    if year is not None:
        where.append("harvest_year=?"); args.append(int(year))
    if harvest_kind is not None:
        where.append("harvest_kind=?"); args.append(harvest_kind)
    if harvest_value is not None:
        where.append("harvest_value=?"); args.append(harvest_value)
    return db.execute(
        "SELECT * FROM companion_external_notice_cache WHERE "
        +" AND ".join(where)+" ORDER BY harvest_year,page_number,id",
        tuple(args),
    ).fetchall()


def _notice_dict(row):
    return {
        "evidence_type":row["evidence_type"],
        "source_record_name":row["source_record_name"],
        "event_type":row["event_type"],
        "event_date":row["event_date"],
        "publication":row["publication"],
        "publication_date":row["publication_date"],
        "details":row["details"],
        "birth_date_claim":row["birth_date_claim"],
        "place_claim":row["place_claim"],
    }


def _surname_token(name: str | None) -> str:
    toks=_norm(name).split()
    return toks[-1] if toks else ""


def candidate_people_for_notice(db, notice_row):
    surname=_surname_token(notice_row["source_record_name"])
    if not surname:
        return []
    people=db.execute(
        """
        SELECT id,gedcom_xref,display_name,given_names,surname
        FROM people
        WHERE lower(trim(COALESCE(surname,'')))=?
        ORDER BY id
        """,
        (surname,),
    ).fetchall()
    return [p for p in people if death_research_state(db,p["id"])["state"] in ("missing","incomplete")]


def _finding_exists(db, person_xref: str, notice_row) -> bool:
    return bool(db.execute(
        """
        SELECT 1
        FROM companion_external_evidence
        WHERE person_gedcom_xref=? AND source_name=?
          AND COALESCE(source_record_name,'')=COALESCE(?, '')
          AND COALESCE(event_date,'')=COALESCE(?, '')
          AND COALESCE(publication_date,'')=COALESCE(?, '')
        LIMIT 1
        """,
        (
            person_xref,RYERSON_SOURCE,notice_row["source_record_name"],
            notice_row["event_date"],notice_row["publication_date"],
        ),
    ).fetchone())


def cross_match_notice(db, notice_id: int, *, minimum_score: int = 55):
    notice=db.execute(
        "SELECT * FROM companion_external_notice_cache WHERE id=?",(notice_id,)
    ).fetchone()
    if not notice:
        raise ValueError("Unknown cached notice")

    evidence=_notice_dict(notice)
    results=[]
    for person in candidate_people_for_notice(db,notice):
        match=match_external_evidence(db,person["id"],evidence)
        if match.status=="reject" or match.score < minimum_score:
            continue

        created=False
        if not _finding_exists(db,person["gedcom_xref"],notice):
            add_external_evidence(
                db,
                person_gedcom_xref=person["gedcom_xref"],
                person_name_snapshot=person["display_name"],
                source_name=RYERSON_SOURCE,
                evidence_type=notice["evidence_type"] or "notice",
                source_record_name=notice["source_record_name"],
                event_type=notice["event_type"],
                event_date=notice["event_date"],
                publication=notice["publication"],
                publication_date=notice["publication_date"],
                details=notice["details"],
                birth_date_claim=notice["birth_date_claim"],
                place_claim=notice["place_claim"],
                match_confidence=match.score,
                match_reason="; ".join(match.reasons),
                review_status="new",
            )
            created=True

        results.append({
            "person_id":person["id"],
            "person_gedcom_xref":person["gedcom_xref"],
            "display_name":person["display_name"],
            "score":match.score,
            "status":match.status,
            "reasons":match.reasons,
            "created":created,
        })
    return sorted(results,key=lambda x:(-x["score"],x["display_name"]))


def cross_match_cached_notices(db, *, year: int | None = None,
                               harvest_kind: str | None = None,
                               harvest_value: str | None = None,
                               minimum_score: int = 55):
    notices=cached_notices(
        db,year=year,harvest_kind=harvest_kind,harvest_value=harvest_value
    )
    matched_notices=0
    findings=0
    created=0
    rows=[]
    for notice in notices:
        matches=cross_match_notice(db,notice["id"],minimum_score=minimum_score)
        if matches:
            matched_notices+=1
            findings+=len(matches)
            created+=sum(1 for m in matches if m["created"])
            rows.append({"notice_id":notice["id"],"matches":matches})
    return {
        "notices_checked":len(notices),
        "matched_notices":matched_notices,
        "findings":findings,
        "created_findings":created,
        "matches":rows,
    }


# RC1.0.14.7.4.7 — multi-harvest notice membership.
_CACHE_HARVEST_ROWS_WITHOUT_MEMBERSHIP = cache_harvest_rows

HARVEST_MEMBERSHIP_SCHEMA = """
CREATE TABLE IF NOT EXISTS companion_external_notice_harvest_membership(
    source_name TEXT NOT NULL,
    record_key TEXT NOT NULL,
    harvest_kind TEXT NOT NULL,
    harvest_value TEXT NOT NULL,
    page_number INTEGER NOT NULL DEFAULT 0,
    first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(source_name,record_key,harvest_kind,harvest_value)
);
CREATE INDEX IF NOT EXISTS idx_companion_external_notice_membership_search
ON companion_external_notice_harvest_membership(
    source_name,harvest_kind,harvest_value
);
"""


def ensure_harvest_membership(db):
    db.executescript(HARVEST_MEMBERSHIP_SCHEMA)
    db.commit()


def harvest_membership_count(db, *, source_name="Ryerson", harvest_kind, harvest_value):
    ensure_harvest_membership(db)
    return int(db.execute(
        """
        SELECT COUNT(*)
        FROM companion_external_notice_harvest_membership
        WHERE source_name=?
          AND harvest_kind=?
          AND lower(trim(harvest_value))=lower(trim(?))
        """,
        (source_name,harvest_kind,harvest_value),
    ).fetchone()[0])


def cache_harvest_rows(
    db,
    rows,
    *,
    harvest_kind,
    harvest_value,
    harvest_year,
    page_number=0,
):
    """Cache each source notice once and always record search membership."""
    ensure_harvest_membership(db)

    result=_CACHE_HARVEST_ROWS_WITHOUT_MEMBERSHIP(
        db,
        rows,
        harvest_kind=harvest_kind,
        harvest_value=harvest_value,
        harvest_year=harvest_year,
        page_number=page_number,
    )

    for row in rows:
        record_key=harvest_record_key(row)
        db.execute(
            """
            INSERT INTO companion_external_notice_harvest_membership(
                source_name,record_key,harvest_kind,harvest_value,page_number,
                first_seen_at,last_seen_at
            ) VALUES('Ryerson',?,?,?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
            ON CONFLICT(source_name,record_key,harvest_kind,harvest_value)
            DO UPDATE SET
                page_number=excluded.page_number,
                last_seen_at=CURRENT_TIMESTAMP
            """,
            (record_key,harvest_kind,harvest_value,int(page_number or 0)),
        )

    db.commit()
    result=dict(result)
    result["memberships"]=len(rows)
    result["membership_count"]=harvest_membership_count(
        db,
        harvest_kind=harvest_kind,
        harvest_value=harvest_value,
    )
    return result
