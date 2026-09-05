from __future__ import annotations

"""Companion-native Recently Explored People.

Recent people use the stable Reunion/GEDCOM xref and are scoped to the active
Family File, so the list survives Safe Refresh GEDCOM replacements without
crossing family-file boundaries.
"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS companion_recent_people_v2(
 workspace_id INTEGER NOT NULL,
 person_gedcom_xref TEXT NOT NULL,
 viewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(workspace_id, person_gedcom_xref)
);
"""


def ensure_person_recents(db):
    db.executescript(SCHEMA)
    db.commit()


def _workspace_id(db):
    from .family_files import active_family_file
    ff = active_family_file(db)
    return int(ff["id"]) if ff else 0


def record_recent_person(db, person_id):
    ensure_person_recents(db)
    row = db.execute(
        "SELECT gedcom_xref FROM people WHERE id=?", (int(person_id),)
    ).fetchone()
    if not row or not row["gedcom_xref"]:
        return False
    db.execute(
        """INSERT INTO companion_recent_people_v2(workspace_id,person_gedcom_xref,viewed_at)
           VALUES(?,?,CURRENT_TIMESTAMP)
           ON CONFLICT(workspace_id,person_gedcom_xref)
           DO UPDATE SET viewed_at=CURRENT_TIMESTAMP""",
        (_workspace_id(db), row["gedcom_xref"]),
    )
    db.commit()
    return True


def recently_explored_people(db, limit=6):
    ensure_person_recents(db)
    limit = max(1, min(20, int(limit or 6)))
    return [dict(r) for r in db.execute(
        """SELECT p.id,p.display_name,p.gedcom_xref,r.viewed_at
           FROM companion_recent_people_v2 r
           JOIN people p ON p.gedcom_xref=r.person_gedcom_xref
           WHERE r.workspace_id=?
           ORDER BY r.viewed_at DESC,p.display_name
           LIMIT ?""",
        (_workspace_id(db), limit),
    ).fetchall()]
