"""Missing-death candidate selection and external evidence identity matching."""

from __future__ import annotations

import re
from datetime import date
from dataclasses import dataclass

from .discovery import research_gaps, relationship_connections


@dataclass(frozen=True)
class MatchResult:
    score: int
    status: str
    reasons: tuple[str, ...]
    contradictions: tuple[str, ...]


def _norm(value: str | None) -> str:
    if not value:
        return ""
    value = value.casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def _tokens(value: str | None) -> list[str]:
    return _norm(value).split()


def _event(db, pid: int, event_type: str):
    return db.execute(
        """
        SELECT *
        FROM events
        WHERE person_id=? AND lower(event_type)=lower(?)
        ORDER BY id
        LIMIT 1
        """,
        (pid, event_type),
    ).fetchone()


def death_research_state(db, pid: int):
    """Classify the structured Death record as missing, incomplete or recorded."""
    row = db.execute(
        "SELECT * FROM events WHERE person_id=? AND lower(event_type)='death' ORDER BY id LIMIT 1",
        (pid,),
    ).fetchone()
    if not row:
        return {
            "state": "missing",
            "event_id": None,
            "date_text": None,
            "place_text": None,
            "note_text": None,
            "has_source": False,
            "has_media": False,
            "reasons": ("No Death event recorded",),
        }

    has_source = bool(db.execute(
        "SELECT 1 FROM event_sources WHERE event_id=? LIMIT 1", (row["id"],)
    ).fetchone())
    has_media = bool(db.execute(
        "SELECT 1 FROM event_media WHERE event_id=? LIMIT 1", (row["id"],)
    ).fetchone())

    reasons = []
    if not (row["date_text"] or "").strip():
        reasons.append("Death date not recorded")
    if not (row["place_text"] or "").strip():
        reasons.append("Death place not recorded")
    if not has_source and not has_media:
        reasons.append("No linked death evidence")

    state = "incomplete" if reasons else "recorded"
    return {
        "state": state,
        "event_id": row["id"],
        "date_text": row["date_text"],
        "place_text": row["place_text"],
        "note_text": row["note_text"],
        "has_source": has_source,
        "has_media": has_media,
        "reasons": tuple(reasons),
    }

def missing_death_candidates(db):
    """Return people whose Death research state is missing or incomplete.

    Birth and Death facts are loaded in bulk without correlated per-person
    event lookups.
    """
    rows = db.execute(
        """
        WITH
        first_birth AS (
            SELECT person_id, MIN(id) AS event_id
            FROM events
            WHERE lower(event_type)='birth'
            GROUP BY person_id
        ),
        first_death AS (
            SELECT person_id, MIN(id) AS event_id
            FROM events
            WHERE lower(event_type)='death'
            GROUP BY person_id
        ),
        sourced_events AS (
            SELECT DISTINCT event_id
            FROM event_sources
        ),
        media_events AS (
            SELECT DISTINCT event_id
            FROM event_media
        )
        SELECT
            p.id AS person_id,
            p.gedcom_xref,
            p.reunion_person_id,
            p.given_names,
            p.surname,
            p.display_name,
            p.sex,
            p.raw_name,

            b.date_text AS birth_date,
            b.place_text AS birth_place,

            d.id AS death_event_id,
            d.date_text AS death_date,
            d.place_text AS death_place,
            d.note_text AS death_note_text,

            CASE WHEN se.event_id IS NOT NULL THEN 1 ELSE 0 END
                AS death_has_source,

            CASE WHEN me.event_id IS NOT NULL THEN 1 ELSE 0 END
                AS death_has_media

        FROM people p

        LEFT JOIN first_birth fb
          ON fb.person_id=p.id
        LEFT JOIN events b
          ON b.id=fb.event_id

        LEFT JOIN first_death fd
          ON fd.person_id=p.id
        LEFT JOIN events d
          ON d.id=fd.event_id

        LEFT JOIN sourced_events se
          ON se.event_id=d.id
        LEFT JOIN media_events me
          ON me.event_id=d.id

        ORDER BY p.surname,p.given_names,p.id
        """
    ).fetchall()

    out = []

    for r in rows:
        reasons = []

        if r["death_event_id"] is None:
            death_state = "missing"
            reasons.append("No Death event recorded")
        else:
            if not (r["death_date"] or "").strip():
                reasons.append("Death date not recorded")

            if not (r["death_place"] or "").strip():
                reasons.append("Death place not recorded")

            if (
                not bool(r["death_has_source"])
                and not bool(r["death_has_media"])
            ):
                reasons.append("No linked death evidence")

            death_state = "incomplete" if reasons else "recorded"

        if death_state not in ("missing", "incomplete"):
            continue

        out.append({
            "person_id": r["person_id"],
            "gedcom_xref": r["gedcom_xref"],
            "display_name": r["display_name"],
            "given_names": r["given_names"],
            "surname": r["surname"],
            "birth_date": r["birth_date"],
            "birth_place": r["birth_place"],
            "death_state": death_state,
            "death_event_id": r["death_event_id"],
            "death_note_text": r["death_note_text"],
            "death_reasons": tuple(reasons),
        })

    return out


def _birth_years(value: str | None) -> tuple[int, ...]:
    years = []
    for token in re.findall(
        r"(?<!\d)(1[5-9]\d{2}|20\d{2})(?!\d)",
        str(value or ""),
    ):
        years.append(int(token))
    return tuple(years)


def ryerson_birth_eligible(
    value: str | None,
    *,
    today: date | None = None,
    max_age: int = 100,
) -> bool:
    # Ryerson discovery needs at least a usable birth year.
    years = _birth_years(value)
    if not years:
        return False

    today = today or date.today()

    # For an uncertain/range date use the latest plausible year.
    # This retains someone if the recorded date could still place
    # them within the 100-year discovery window.
    latest_year = max(years)
    return (today.year - latest_year) <= max_age


def _usable_surname(value: str | None) -> bool:
    surname=(value or "").strip()
    if len(surname) < 2:
        return False
    return bool(re.search(r"[A-Za-z]",surname))


def _ryerson_priority(db, row: dict, *, include_relationships: bool = True) -> tuple[int, tuple[str, ...]]:
    score=10
    reasons=["usable surname"]
    given=(row.get("given_names") or "").strip()
    if given:
        score+=20
        reasons.append("given name recorded")
        if len(given.split()) > 1:
            score+=5
            reasons.append("multiple given names")
    if row.get("birth_date"):
        score+=30
        reasons.append("birth date recorded")
    if row.get("birth_place"):
        score+=10
        reasons.append("birth place recorded")
    if row.get("death_state")=="incomplete":
        score+=10
        reasons.append("existing Death event")
    if row.get("death_note_text"):
        score+=15
        reasons.append("Death event note available")
    if include_relationships:
        rel=relationship_connections(db,row["person_id"])
        if rel["spouses"]:
            score+=10
            reasons.append("spouse recorded")
        if rel["parents"]:
            score+=10
            reasons.append("parents recorded")
        if rel["children"]:
            score+=5
            reasons.append("children recorded")
    return score,tuple(reasons)


def ryerson_death_candidates(db):
    # Ryerson discovery is intentionally narrower than the general
    # missing-death research list.
    #
    # Fetch birth/death facts in bulk rather than performing thousands
    # of per-person event and relationship queries.
    raw = db.execute(
        """
        SELECT
            p.id AS person_id,
            p.gedcom_xref,
            p.display_name,
            p.given_names,
            p.surname,

            b.date_text AS birth_date,
            b.place_text AS birth_place,

            d.id AS death_event_id,
            d.date_text AS death_date,
            d.place_text AS death_place,
            d.note_text AS death_note_text,

            EXISTS(
                SELECT 1
                FROM event_sources es
                WHERE es.event_id=d.id
            ) AS death_has_source,

            EXISTS(
                SELECT 1
                FROM event_media em
                WHERE em.event_id=d.id
            ) AS death_has_media

        FROM people p

        JOIN events b
          ON b.id=(
              SELECT b2.id
              FROM events b2
              WHERE b2.person_id=p.id
                AND lower(b2.event_type)='birth'
              ORDER BY b2.id
              LIMIT 1
          )

        LEFT JOIN events d
          ON d.id=(
              SELECT d2.id
              FROM events d2
              WHERE d2.person_id=p.id
                AND lower(d2.event_type)='death'
              ORDER BY d2.id
              LIMIT 1
          )

        ORDER BY p.surname,p.given_names,p.id
        """
    ).fetchall()

    out = []

    for r in raw:
        birth_date = r["birth_date"]

        # No usable birth date, or potential age beyond 100:
        # do not put this person into Ryerson discovery.
        if not ryerson_birth_eligible(birth_date):
            continue

        if not _usable_surname(r["surname"]):
            continue

        reasons = []

        if r["death_event_id"] is None:
            death_state = "missing"
            reasons.append("No Death event recorded")
        else:
            if not (r["death_date"] or "").strip():
                reasons.append("Death date not recorded")

            if not (r["death_place"] or "").strip():
                reasons.append("Death place not recorded")

            if (
                not bool(r["death_has_source"])
                and not bool(r["death_has_media"])
            ):
                reasons.append("No linked death evidence")

            death_state = "incomplete" if reasons else "recorded"

        if death_state == "recorded":
            continue

        row = {
            "person_id": r["person_id"],
            "gedcom_xref": r["gedcom_xref"],
            "display_name": r["display_name"],
            "given_names": r["given_names"],
            "surname": r["surname"],
            "birth_date": birth_date,
            "birth_place": r["birth_place"],
            "death_state": death_state,
            "death_event_id": r["death_event_id"],
            "death_note_text": r["death_note_text"],
            "death_reasons": tuple(reasons),
        }

        # Recent is now the normal Priorities mode.
        # Do not calculate spouse/parent/child relationships simply
        # to build the background Ryerson candidate list.
        score, priority_reasons = _ryerson_priority(
            db,
            row,
            include_relationships=False,
        )

        row["ryerson_priority"] = score
        row["ryerson_priority_reasons"] = priority_reasons
        out.append(row)

    out.sort(
        key=lambda r: (
            -r["ryerson_priority"],
            (r.get("surname") or "").casefold(),
            (r.get("given_names") or "").casefold(),
            r["person_id"],
        )
    )
    return out


def person_identity_profile(db, pid: int):
    p = db.execute(
        """
        SELECT id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name
        FROM people WHERE id=?
        """,
        (pid,),
    ).fetchone()
    if not p:
        return None

    birth = _event(db, pid, "Birth")
    rel = relationship_connections(db, pid)
    return {
        "person_id": p["id"],
        "gedcom_xref": p["gedcom_xref"],
        "display_name": p["display_name"],
        "given_names": p["given_names"],
        "surname": p["surname"],
        "birth_date": birth["date_text"] if birth else None,
        "birth_place": birth["place_text"] if birth else None,
        "parents": [r["display_name"] for r in rel["parents"]],
        "spouses": [r["display_name"] for r in rel["spouses"]],
        "children": [r["display_name"] for r in rel["children"]],
    }


def _name_score(profile, source_record_name: str | None):
    reasons = []
    contradictions = []
    score = 0

    source = _norm(source_record_name)
    source_tokens = _tokens(source_record_name)
    person_tokens = _tokens(profile.get("display_name"))
    surname = _norm(profile.get("surname"))

    if surname:
        if surname in source_tokens:
            score += 30
            reasons.append("surname exact")
        elif source:
            contradictions.append("surname differs")

    if source and source == _norm(profile.get("display_name")):
        score += 45
        reasons.append("full name exact")
        return score, reasons, contradictions

    given = _tokens(profile.get("given_names"))
    if given and source_tokens:
        first = given[0]
        if first in source_tokens:
            score += 15
            reasons.append("first name exact")
        else:
            contradictions.append("first name differs")

        middle = given[1:]
        if middle:
            middle_hits = sum(1 for token in middle if token in source_tokens)
            if middle_hits:
                score += min(10, middle_hits * 5)
                reasons.append("middle name supported")
            else:
                # Small tolerance for a one-character spelling variation such as
                # Stanly/Stanley. It is evidence, not an automatic correction.
                for m in middle:
                    for st in source_tokens:
                        if abs(len(m) - len(st)) <= 1 and _levenshtein(m, st) == 1:
                            score += 5
                            reasons.append("middle name near-match")
                            return score, reasons, contradictions

    return score, reasons, contradictions


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(
                min(
                    cur[-1] + 1,
                    prev[j] + 1,
                    prev[j - 1] + (ca != cb),
                )
            )
        prev = cur
    return prev[-1]


def match_external_evidence(db, pid: int, evidence: dict) -> MatchResult:
    profile = person_identity_profile(db, pid)
    if not profile:
        return MatchResult(0, "reject", (), ("person not found",))

    score, reasons, contradictions = _name_score(
        profile, evidence.get("source_record_name")
    )

    claim_birth = evidence.get("birth_date_claim")
    if claim_birth and profile.get("birth_date"):
        if _norm(claim_birth) == _norm(profile["birth_date"]):
            score += 40
            reasons.append("birth date exact")
        else:
            contradictions.append("birth date conflicts")
            score -= 45

    claim_place = evidence.get("place_claim")
    if claim_place and profile.get("birth_place"):
        cp = _norm(claim_place)
        bp = _norm(profile["birth_place"])
        if cp and bp and (cp in bp or bp in cp):
            score += 10
            reasons.append("place consistent")

    # Relationship names are strong corroboration when present in notice details.
    details = _norm(evidence.get("details"))
    for label, names in (
        ("spouse", profile["spouses"]),
        ("child", profile["children"]),
        ("parent", profile["parents"]),
    ):
        for name in names:
            toks = _tokens(name)
            if toks and all(tok in details.split() for tok in toks if len(tok) > 2):
                score += 10
                reasons.append(f"{label} corroborated")
                break

    score = max(0, min(100, score))

    if "birth date conflicts" in contradictions:
        status = "reject"
    elif score >= 80:
        status = "high_confidence"
    elif score >= 55:
        status = "needs_review"
    else:
        status = "reject"

    return MatchResult(
        score=score,
        status=status,
        reasons=tuple(reasons),
        contradictions=tuple(contradictions),
    )
