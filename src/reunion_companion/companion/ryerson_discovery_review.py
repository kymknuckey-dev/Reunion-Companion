from __future__ import annotations

from datetime import datetime, timezone

DISCOVERY_STATES = (
    "new",
    "deferred",
    "waiting_for_reunion",
    "already_known",
    "rejected",
    "confirmed_complete",
    "ineligible",
)


def _utcnow():
    return datetime.now(timezone.utc).isoformat()


_STATE_PRIORITY = {
    "new": 0,
    "ineligible": 1,
    "deferred": 2,
    "waiting_for_reunion": 3,
    "already_known": 4,
    "rejected": 4,
    "confirmed_complete": 5,
}

def _preferred_discovery_row(rows):
    """Choose the durable decision when one external record has legacy duplicates."""
    return max(
        rows,
        key=lambda row: (
            _STATE_PRIORITY.get(str(row["state"] or "new"), 0),
            str(row["reviewed_at"] or ""),
            str(row["updated_at"] or ""),
            -int(row["id"]),
        ),
    )

def consolidate_discovery_record_identity(db):
    """Collapse legacy review rows to one lifecycle per external source record.

    proposed_fact_key is an interpretation of a source record and can change as
    parsing improves.  It must not be part of the durable review identity.
    """
    groups=db.execute(
        """SELECT person_id,source_name,external_record_key,COUNT(*) n
           FROM companion_external_discovery_review
           GROUP BY person_id,source_name,external_record_key HAVING COUNT(*)>1"""
    ).fetchall()
    removed=0
    for group in groups:
        rows=db.execute(
            """SELECT * FROM companion_external_discovery_review
               WHERE person_id=? AND source_name=? AND external_record_key=? ORDER BY id""",
            (group["person_id"],group["source_name"],group["external_record_key"]),
        ).fetchall()
        keep=_preferred_discovery_row(rows)
        for row in rows:
            if int(row["id"])==int(keep["id"]):
                continue
            db.execute("DELETE FROM companion_external_discovery_review WHERE id=?",(row["id"],))
            removed+=1
    if removed:
        db.commit()
    return removed


def ensure_discovery_review_schema(db):
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS companion_external_discovery_review (
            id INTEGER PRIMARY KEY,
            person_id INTEGER NOT NULL,
            source_name TEXT NOT NULL,
            external_record_key TEXT NOT NULL,
            proposed_fact_key TEXT NOT NULL DEFAULT '',
            match_confidence INTEGER,
            state TEXT NOT NULL DEFAULT 'new',
            decision_note TEXT NOT NULL DEFAULT '',
            first_seen_at TEXT NOT NULL,
            reviewed_at TEXT,
            confirmed_at TEXT,
            updated_at TEXT NOT NULL,
            UNIQUE(person_id, source_name, external_record_key, proposed_fact_key)
        )
        """
    )
    columns={row["name"] for row in db.execute("PRAGMA table_info(companion_external_discovery_review)").fetchall()}
    if "match_confidence" not in columns:
        db.execute("ALTER TABLE companion_external_discovery_review ADD COLUMN match_confidence INTEGER")
    consolidate_discovery_record_identity(db)
    db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_external_discovery_review_state
        ON companion_external_discovery_review(state, person_id)
        """
    )
    db.commit()


def remember_discovery(
    db,
    *,
    person_id: int,
    source_name: str,
    external_record_key: str,
    proposed_fact_key: str = "",
    match_confidence: int | None = None,
    now: str | None = None,
):
    ensure_discovery_review_schema(db)
    stamp = now or _utcnow()

    existing=db.execute(
        """SELECT * FROM companion_external_discovery_review
           WHERE person_id=? AND source_name=? AND external_record_key=?
           ORDER BY id LIMIT 1""",
        (person_id,source_name,external_record_key),
    ).fetchone()
    if existing is not None:
        # Parsing may reinterpret a notice (for example a publication-only
        # notice no longer proposing a Death). Preserve the review lifecycle.
        if match_confidence is not None:
            db.execute(
                "UPDATE companion_external_discovery_review SET match_confidence=?,updated_at=? WHERE id=?",
                (int(match_confidence),stamp,existing["id"]),
            )
            db.commit()
        return db.execute("SELECT * FROM companion_external_discovery_review WHERE id=?",(existing["id"],)).fetchone()

    db.execute(
        """INSERT INTO companion_external_discovery_review
           (person_id,source_name,external_record_key,proposed_fact_key,match_confidence,state,decision_note,first_seen_at,updated_at)
           VALUES (?,?,?,?,?,'new','',?,?)""",
        (person_id,source_name,external_record_key,proposed_fact_key,
         int(match_confidence) if match_confidence is not None else None,stamp,stamp),
    )
    db.commit()
    return db.execute(
        """SELECT * FROM companion_external_discovery_review
           WHERE person_id=? AND source_name=? AND external_record_key=? ORDER BY id LIMIT 1""",
        (person_id,source_name,external_record_key),
    ).fetchone()



def reconcile_discovery_eligibility(db, eligible_person_ids):
    """Retire untouched discoveries that no longer qualify for research review."""
    from .ryerson_discovery_assembly import _definite_date

    ensure_discovery_review_schema(db)
    eligible = {int(pid) for pid in eligible_person_ids}

    rows = db.execute(
        """
        SELECT
            id,
            person_id,
            proposed_fact_key
        FROM companion_external_discovery_review
        WHERE state='new'
        """
    ).fetchall()

    birth_rows = db.execute(
        """
        SELECT person_id,date_text
        FROM events
        WHERE lower(event_type)='birth'
        ORDER BY person_id,id
        """
    ).fetchall()

    birth_dates = {}
    for birth_row in birth_rows:
        pid = int(birth_row["person_id"])
        if pid in birth_dates:
            continue
        parsed = _definite_date(birth_row["date_text"])
        if parsed is not None:
            birth_dates[pid] = parsed

    stale_person = []
    impossible_chronology = []

    for row in rows:
        person_id = int(row["person_id"])

        if person_id not in eligible:
            stale_person.append(row["id"])
            continue

        fact = str(row["proposed_fact_key"] or "").strip()
        if ":" not in fact:
            continue

        kind, raw_date = fact.split(":", 1)
        if kind.casefold() != "death":
            continue

        birth_date = birth_dates.get(person_id)
        death_date = _definite_date(raw_date)

        if (
            birth_date is not None
            and death_date is not None
            and death_date < birth_date
        ):
            impossible_chronology.append(row["id"])

    if stale_person:
        db.executemany(
            """
            UPDATE companion_external_discovery_review
            SET state='ineligible',
                decision_note='Person no longer meets current external research eligibility rules'
            WHERE id=? AND state='new'
            """,
            [(rid,) for rid in stale_person],
        )

    if impossible_chronology:
        db.executemany(
            """
            UPDATE companion_external_discovery_review
            SET state='ineligible',
                decision_note='Candidate death occurs before the recorded birth'
            WHERE id=? AND state='new'
            """,
            [(rid,) for rid in impossible_chronology],
        )

    if stale_person or impossible_chronology:
        db.commit()

    return len(stale_person) + len(impossible_chronology)


def set_discovery_state(
    db,
    discovery_id: int,
    state: str,
    *,
    note: str = "",
    now: str | None = None,
):
    if state not in DISCOVERY_STATES:
        raise ValueError(f"unsupported discovery state: {state}")

    ensure_discovery_review_schema(db)
    stamp = now or _utcnow()

    reviewed_at = stamp if state != "new" else None
    confirmed_at = stamp if state == "confirmed_complete" else None

    db.execute(
        """
        UPDATE companion_external_discovery_review
        SET state=?,
            decision_note=?,
            reviewed_at=COALESCE(?, reviewed_at),
            confirmed_at=COALESCE(?, confirmed_at),
            updated_at=?
        WHERE id=?
        """,
        (
            state,
            note,
            reviewed_at,
            confirmed_at,
            stamp,
            discovery_id,
        ),
    )
    db.commit()

    return db.execute(
        "SELECT * FROM companion_external_discovery_review WHERE id=?",
        (discovery_id,),
    ).fetchone()


def discovery_counts(db):
    ensure_discovery_review_schema(db)

    counts = {state: 0 for state in DISCOVERY_STATES}
    for row in db.execute(
        """
        SELECT state, COUNT(*) AS n
        FROM companion_external_discovery_review
        GROUP BY state
        """
    ):
        counts[row["state"]] = int(row["n"])

    return counts


def discoveries_for_person(db, person_id: int):
    ensure_discovery_review_schema(db)

    return db.execute(
        """
        SELECT *
        FROM companion_external_discovery_review
        WHERE person_id=?
        ORDER BY
          CASE state
            WHEN 'new' THEN 0
            WHEN 'deferred' THEN 1
            WHEN 'waiting_for_reunion' THEN 2
            WHEN 'already_known' THEN 3
            WHEN 'rejected' THEN 4
            WHEN 'confirmed_complete' THEN 5
            ELSE 9
          END,
          first_seen_at DESC,
          id DESC
        """,
        (person_id,),
    ).fetchall()


def discovery_fact_present_in_reunion(db, discovery) -> bool:
    """Return True only when the proposed fact is definitely present in Reunion."""
    from .ryerson_discovery_assembly import _definite_date

    fact = str(discovery["proposed_fact_key"] or "").strip()
    # Some accepted Ryerson evidence (for example a publication-only notice)
    # is useful corroborating evidence but does not propose a Reunion fact.
    # There is therefore nothing for a later GEDCOM refresh to wait for.
    if not fact:
        return True

    # Historical compatibility: earlier person-level materialisation treated
    # funeral-notice event_date as a proposed Death date.  That can strand an
    # already accepted funeral notice in Waiting for Reunion forever because
    # the notice/publication date is not a second death date.  Resolve those
    # legacy rows as evidence-only when the linked stored Ryerson finding says
    # it is a funeral/publication notice.
    source_name = str(discovery["source_name"] or "").casefold()
    external_key = str(discovery["external_record_key"] or "")
    if source_name == "ryerson" and external_key.startswith("ryerson:"):
        evidence_id = external_key.split(":", 1)[1]
        if evidence_id.isdigit():
            evidence = db.execute(
                "SELECT evidence_type,event_type FROM companion_external_evidence WHERE id=?",
                (int(evidence_id),),
            ).fetchone()
            if evidence is not None:
                evidence_type = str(evidence["evidence_type"] or "").casefold()
                event_type = str(evidence["event_type"] or "").casefold()
                if "funeral" in evidence_type or event_type == "publication":
                    return True
    if ":" not in fact:
        return False

    kind, raw_date = fact.split(":", 1)
    proposed_date = _definite_date(raw_date)
    if proposed_date is None:
        return False

    event_type = {
        "death": "death",
        "funeral": "funeral",
    }.get(kind.casefold())

    if event_type is None:
        return False

    rows = db.execute(
        """
        SELECT date_text
        FROM events
        WHERE person_id=?
          AND lower(event_type)=?
        ORDER BY id
        """,
        (int(discovery["person_id"]), event_type),
    ).fetchall()

    for row in rows:
        recorded_date = _definite_date(row["date_text"])
        if recorded_date is not None and recorded_date == proposed_date:
            return True

    return False


def reconcile_waiting_discoveries(
    db,
    fact_present_fn,
    *,
    now: str | None = None,
):
    """Confirm accepted discoveries whose proposed fact now exists after GEDCOM refresh."""
    ensure_discovery_review_schema(db)
    stamp = now or _utcnow()

    confirmed = []
    rows = db.execute(
        """
        SELECT *
        FROM companion_external_discovery_review
        WHERE state='waiting_for_reunion'
        ORDER BY id
        """
    ).fetchall()

    for row in rows:
        if fact_present_fn(row):
            set_discovery_state(
                db,
                row["id"],
                "confirmed_complete",
                note=row["decision_note"],
                now=stamp,
            )
            confirmed.append(row["id"])

    return confirmed
