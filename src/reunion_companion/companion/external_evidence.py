"""Companion-owned external evidence persistence.

External evidence is deliberately separate from imported Reunion/GEDCOM data.
The durable person link is the GEDCOM xref, not the transient SQLite people.id.
"""

from __future__ import annotations


SCHEMA = """
CREATE TABLE IF NOT EXISTS companion_external_evidence(
    id INTEGER PRIMARY KEY,
    person_gedcom_xref TEXT NOT NULL,
    person_name_snapshot TEXT,
    source_name TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    source_record_name TEXT,
    event_type TEXT,
    event_date TEXT,
    publication TEXT,
    publication_date TEXT,
    details TEXT,
    birth_date_claim TEXT,
    place_claim TEXT,
    match_confidence INTEGER,
    match_reason TEXT,
    review_status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_companion_external_evidence_person_xref
ON companion_external_evidence(person_gedcom_xref);

CREATE INDEX IF NOT EXISTS idx_companion_external_evidence_status
ON companion_external_evidence(review_status);

CREATE TABLE IF NOT EXISTS companion_external_scan_queue(
    id INTEGER PRIMARY KEY,
    source_name TEXT NOT NULL,
    person_gedcom_xref TEXT NOT NULL,
    person_name_snapshot TEXT,
    status TEXT NOT NULL DEFAULT 'queued',
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    last_attempt_at TEXT,
    next_retry_at TEXT,
    completed_at TEXT,
    result_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_name,person_gedcom_xref)
);

CREATE INDEX IF NOT EXISTS idx_companion_external_scan_status
ON companion_external_scan_queue(source_name,status,next_retry_at);

CREATE TABLE IF NOT EXISTS companion_external_notice_cache(
    id INTEGER PRIMARY KEY,
    source_name TEXT NOT NULL,
    record_key TEXT NOT NULL,
    harvest_kind TEXT NOT NULL,
    harvest_value TEXT NOT NULL,
    harvest_year INTEGER NOT NULL,
    page_number INTEGER NOT NULL DEFAULT 1,
    evidence_type TEXT,
    source_record_name TEXT,
    event_type TEXT,
    event_date TEXT,
    publication TEXT,
    publication_date TEXT,
    details TEXT,
    birth_date_claim TEXT,
    place_claim TEXT,
    normalized_json TEXT NOT NULL,
    first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_name,record_key)
);

CREATE INDEX IF NOT EXISTS idx_companion_external_notice_harvest
ON companion_external_notice_cache(source_name,harvest_kind,harvest_value,harvest_year);

CREATE TABLE IF NOT EXISTS companion_ryerson_surname_queue(
    id INTEGER PRIMARY KEY,
    surname TEXT NOT NULL,
    surname_key TEXT NOT NULL UNIQUE,
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

CREATE INDEX IF NOT EXISTS idx_companion_ryerson_surname_queue_status
ON companion_ryerson_surname_queue(status,next_retry_at,people_count);

CREATE TABLE IF NOT EXISTS companion_ryerson_surname_progress(
    surname_key TEXT PRIMARY KEY,
    surname TEXT NOT NULL,
    current_page INTEGER NOT NULL DEFAULT 0,
    current_url TEXT,
    pages_completed INTEGER NOT NULL DEFAULT 0,
    rows_seen INTEGER NOT NULL DEFAULT 0,
    inserted_rows INTEGER NOT NULL DEFAULT 0,
    existing_rows INTEGER NOT NULL DEFAULT 0,
    is_complete INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

VALID_STATUSES = {"new", "reviewed", "accepted", "rejected"}


def ensure_external_evidence(db) -> None:
    db.executescript(SCHEMA)
    db.commit()


def add_external_evidence(
    db,
    *,
    person_gedcom_xref: str,
    person_name_snapshot: str | None,
    source_name: str,
    evidence_type: str,
    source_record_name: str | None = None,
    event_type: str | None = None,
    event_date: str | None = None,
    publication: str | None = None,
    publication_date: str | None = None,
    details: str | None = None,
    birth_date_claim: str | None = None,
    place_claim: str | None = None,
    match_confidence: int | None = None,
    match_reason: str | None = None,
    review_status: str = "new",
) -> int:
    if review_status not in VALID_STATUSES:
        raise ValueError(f"Unsupported review_status: {review_status}")
    if match_confidence is not None and not 0 <= int(match_confidence) <= 100:
        raise ValueError("match_confidence must be between 0 and 100")

    # External searches can legitimately rediscover the same source record on a
    # later pass (for example a grouped ``Bickle, John`` Ryerson search).  The
    # evidence store must therefore be idempotent for a person/source finding.
    # Keep this guard here, at the common insertion boundary, so every ingest
    # path (runner, harvest cross-match and browser assist) gets the same
    # protection.  Existing databases may already contain duplicates, so this
    # deliberately does not rely on adding a UNIQUE index during migration.
    existing = db.execute(
        """
        SELECT id
        FROM companion_external_evidence
        WHERE person_gedcom_xref=?
          AND source_name=?
          AND COALESCE(source_record_name,'')=COALESCE(?, '')
          AND COALESCE(event_type,'')=COALESCE(?, '')
          AND COALESCE(event_date,'')=COALESCE(?, '')
          AND COALESCE(publication_date,'')=COALESCE(?, '')
        ORDER BY id
        LIMIT 1
        """,
        (
            person_gedcom_xref,
            source_name,
            source_record_name,
            event_type,
            event_date,
            publication_date,
        ),
    ).fetchone()
    if existing:
        return int(existing["id"])

    cur = db.execute(
        """
        INSERT INTO companion_external_evidence(
            person_gedcom_xref,person_name_snapshot,source_name,evidence_type,
            source_record_name,event_type,event_date,publication,publication_date,
            details,birth_date_claim,place_claim,match_confidence,match_reason,
            review_status
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            person_gedcom_xref,
            person_name_snapshot,
            source_name,
            evidence_type,
            source_record_name,
            event_type,
            event_date,
            publication,
            publication_date,
            details,
            birth_date_claim,
            place_claim,
            match_confidence,
            match_reason,
            review_status,
        ),
    )
    db.commit()
    return int(cur.lastrowid)


def external_evidence_for_person(db, person_gedcom_xref: str):
    return db.execute(
        """
        SELECT *
        FROM companion_external_evidence
        WHERE person_gedcom_xref=?
        ORDER BY id
        """,
        (person_gedcom_xref,),
    ).fetchall()


def set_external_evidence_status(db, evidence_id: int, review_status: str) -> None:
    if review_status not in VALID_STATUSES:
        raise ValueError(f"Unsupported review_status: {review_status}")
    db.execute(
        """
        UPDATE companion_external_evidence
        SET review_status=?,updated_at=CURRENT_TIMESTAMP
        WHERE id=?
        """,
        (review_status, evidence_id),
    )
    db.commit()


def external_evidence_with_current_person(db, person_gedcom_xref: str):
    """Return findings joined to the current imported person when present."""
    return db.execute(
        """
        SELECT ce.*,p.id AS current_person_id,p.display_name AS current_person_name
        FROM companion_external_evidence ce
        LEFT JOIN people p ON p.gedcom_xref=ce.person_gedcom_xref
        WHERE ce.person_gedcom_xref=?
        ORDER BY ce.id
        """,
        (person_gedcom_xref,),
    ).fetchall()


def consolidate_external_evidence_duplicates(db) -> int:
    """Collapse historical exact duplicate evidence and preserve review state.

    The canonical evidence row is the oldest id. Discovery review references are
    repointed before duplicate evidence is deleted; review lifecycle consolidation
    then ensures the same logical source record is represented only once.
    """
    from .ryerson_discovery_review import ensure_discovery_review_schema, consolidate_discovery_record_identity

    ensure_external_evidence(db)
    ensure_discovery_review_schema(db)
    groups=db.execute(
        """
        SELECT person_gedcom_xref,source_name,COALESCE(source_record_name,'') record_name,
               COALESCE(event_type,'') event_type,COALESCE(event_date,'') event_date,
               COALESCE(publication_date,'') publication_date,COUNT(*) n
        FROM companion_external_evidence
        GROUP BY person_gedcom_xref,source_name,record_name,event_type,event_date,publication_date
        HAVING COUNT(*)>1
        """
    ).fetchall()
    removed=0
    for g in groups:
        rows=db.execute(
            """SELECT id FROM companion_external_evidence
               WHERE person_gedcom_xref=? AND source_name=?
                 AND COALESCE(source_record_name,'')=? AND COALESCE(event_type,'')=?
                 AND COALESCE(event_date,'')=? AND COALESCE(publication_date,'')=?
               ORDER BY id""",
            (g['person_gedcom_xref'],g['source_name'],g['record_name'],g['event_type'],g['event_date'],g['publication_date']),
        ).fetchall()
        canonical=int(rows[0]['id'])
        for row in rows[1:]:
            duplicate=int(row['id'])
            old_key=f"ryerson:{duplicate}"
            new_key=f"ryerson:{canonical}"
            review_rows=db.execute(
                "SELECT * FROM companion_external_discovery_review WHERE source_name='Ryerson' AND external_record_key=? ORDER BY id",
                (old_key,),
            ).fetchall()
            for review in review_rows:
                targets=db.execute(
                    """SELECT * FROM companion_external_discovery_review
                       WHERE person_id=? AND source_name='Ryerson' AND external_record_key=? ORDER BY id""",
                    (review['person_id'],new_key),
                ).fetchall()
                if targets:
                    from .ryerson_discovery_review import _preferred_discovery_row
                    preferred=_preferred_discovery_row(list(targets)+[review])
                    target=targets[0]
                    if int(preferred['id'])==int(review['id']):
                        db.execute(
                            """UPDATE companion_external_discovery_review SET state=?,decision_note=?,reviewed_at=?,confirmed_at=?,updated_at=?,match_confidence=? WHERE id=?""",
                            (review['state'],review['decision_note'],review['reviewed_at'],review['confirmed_at'],review['updated_at'],review['match_confidence'],target['id']),
                        )
                    db.execute("DELETE FROM companion_external_discovery_review WHERE id=?",(review['id'],))
                else:
                    db.execute("UPDATE companion_external_discovery_review SET external_record_key=? WHERE id=?",(new_key,review['id']))
            db.execute("DELETE FROM companion_external_evidence WHERE id=?",(duplicate,))
            removed+=1
        consolidate_discovery_record_identity(db)
    if removed:
        db.commit()
    return removed
