from __future__ import annotations

"""Companion-native Bookmarked People.

Bookmarks deliberately use the Reunion/GEDCOM xref rather than Companion's
transient people.id so they survive Safe Refresh GEDCOM replacements.
"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS companion_person_bookmarks(
 workspace_id INTEGER NOT NULL,
 person_gedcom_xref TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(workspace_id, person_gedcom_xref)
);
"""


def ensure_person_bookmarks(db):
    db.executescript(SCHEMA)
    db.commit()


def _workspace_id(db):
    from .family_files import active_family_file
    ff = active_family_file(db)
    return int(ff["id"]) if ff else 0


def is_bookmarked(db, person_id):
    ensure_person_bookmarks(db)
    row = db.execute("SELECT gedcom_xref FROM people WHERE id=?", (int(person_id),)).fetchone()
    if not row or not row["gedcom_xref"]:
        return False
    return db.execute(
        "SELECT 1 FROM companion_person_bookmarks WHERE workspace_id=? AND person_gedcom_xref=?",
        (_workspace_id(db), row["gedcom_xref"]),
    ).fetchone() is not None


def set_bookmarked(db, person_id, bookmarked=True):
    ensure_person_bookmarks(db)
    row = db.execute("SELECT gedcom_xref FROM people WHERE id=?", (int(person_id),)).fetchone()
    if not row or not row["gedcom_xref"]:
        raise ValueError("This person has no stable Reunion/GEDCOM identity and cannot be bookmarked.")
    key = (_workspace_id(db), row["gedcom_xref"])
    if bookmarked:
        db.execute(
            "INSERT OR IGNORE INTO companion_person_bookmarks(workspace_id,person_gedcom_xref) VALUES(?,?)",
            key,
        )
    else:
        db.execute(
            "DELETE FROM companion_person_bookmarks WHERE workspace_id=? AND person_gedcom_xref=?",
            key,
        )
    db.commit()


def bookmarked_people(db):
    ensure_person_bookmarks(db)
    return [dict(r) for r in db.execute(
        """SELECT p.id,p.display_name,p.gedcom_xref,b.created_at
           FROM companion_person_bookmarks b
           JOIN people p ON p.gedcom_xref=b.person_gedcom_xref
           WHERE b.workspace_id=?
           ORDER BY b.created_at,p.display_name""",
        (_workspace_id(db),),
    ).fetchall()]
