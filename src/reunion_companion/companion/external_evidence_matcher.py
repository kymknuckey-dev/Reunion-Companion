"""Missing-death candidate selection and external evidence identity matching."""

from __future__ import annotations

import re
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
    """Return people whose Death research state is missing or incomplete."""
    rows = []
    for p in db.execute(
        """
        SELECT id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name
        FROM people
        ORDER BY surname,given_names,id
        """
    ):
        death = death_research_state(db, p["id"])
        if death["state"] in ("missing", "incomplete"):
            birth = _event(db, p["id"], "Birth")
            rows.append({
                "person_id": p["id"],
                "gedcom_xref": p["gedcom_xref"],
                "display_name": p["display_name"],
                "given_names": p["given_names"],
                "surname": p["surname"],
                "birth_date": birth["date_text"] if birth else None,
                "birth_place": birth["place_text"] if birth else None,
                "death_state": death["state"],
                "death_event_id": death["event_id"],
                "death_note_text": death["note_text"],
                "death_reasons": death["reasons"],
            })
    return rows
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
