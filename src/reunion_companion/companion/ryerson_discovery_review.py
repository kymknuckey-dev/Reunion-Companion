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


def ensure_discovery_review_schema(db):
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS companion_external_discovery_review (
            id INTEGER PRIMARY KEY,
            person_id INTEGER NOT NULL,
            source_name TEXT NOT NULL,
            external_record_key TEXT NOT NULL,
            proposed_fact_key TEXT NOT NULL DEFAULT '',
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
    now: str | None = None,
):
    ensure_discovery_review_schema(db)
    stamp = now or _utcnow()

    db.execute(
        """
        INSERT OR IGNORE INTO companion_external_discovery_review
        (
            person_id,
            source_name,
            external_record_key,
            proposed_fact_key,
            state,
            decision_note,
            first_seen_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, 'new', '', ?, ?)
        """,
        (
            person_id,
            source_name,
            external_record_key,
            proposed_fact_key,
            stamp,
            stamp,
        ),
    )
    db.commit()

    return db.execute(
        """
        SELECT *
        FROM companion_external_discovery_review
        WHERE person_id=?
          AND source_name=?
          AND external_record_key=?
          AND proposed_fact_key=?
        """,
        (
            person_id,
            source_name,
            external_record_key,
            proposed_fact_key,
        ),
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
