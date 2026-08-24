from pathlib import Path
import sqlite3
SCHEMA_VERSION=9
SCHEMA="""
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS imports(id INTEGER PRIMARY KEY,source_path TEXT NOT NULL,source_type TEXT NOT NULL,imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS people(id INTEGER PRIMARY KEY,gedcom_xref TEXT UNIQUE,reunion_person_id INTEGER,given_names TEXT,surname TEXT,display_name TEXT NOT NULL,sex TEXT,raw_name TEXT);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,event_type TEXT NOT NULL,date_text TEXT,place_text TEXT,value_text TEXT,note_text TEXT,gedcom_tag TEXT);
CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY,person_id INTEGER REFERENCES people(id) ON DELETE CASCADE,note_type TEXT NOT NULL DEFAULT 'Note',gedcom_tag TEXT,gedcom_note_xref TEXT,text TEXT NOT NULL,is_referenced INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS families(id INTEGER PRIMARY KEY,gedcom_xref TEXT UNIQUE,marriage_date TEXT,marriage_place TEXT);
CREATE TABLE IF NOT EXISTS family_members(family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,role TEXT NOT NULL,PRIMARY KEY(family_id,person_id,role));
CREATE TABLE IF NOT EXISTS media(id INTEGER PRIMARY KEY,gedcom_xref TEXT,file_path TEXT NOT NULL,title TEXT,media_type TEXT,exists_on_disk INTEGER NOT NULL DEFAULT 0,attachment_scope TEXT,attachment_label TEXT,is_preferred INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS person_media(person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,media_id INTEGER NOT NULL REFERENCES media(id) ON DELETE CASCADE,relation TEXT NOT NULL DEFAULT 'GEDCOM',PRIMARY KEY(person_id,media_id,relation));
CREATE TABLE IF NOT EXISTS event_media(event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,media_id INTEGER NOT NULL REFERENCES media(id) ON DELETE CASCADE,relation TEXT NOT NULL DEFAULT 'GEDCOM',PRIMARY KEY(event_id,media_id,relation));
CREATE TABLE IF NOT EXISTS family_media(family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,media_id INTEGER NOT NULL REFERENCES media(id) ON DELETE CASCADE,relation TEXT NOT NULL DEFAULT 'GEDCOM',PRIMARY KEY(family_id,media_id,relation));
CREATE TABLE IF NOT EXISTS sources(id INTEGER PRIMARY KEY,gedcom_xref TEXT UNIQUE,title TEXT,text TEXT,source_type TEXT,display_text TEXT);
CREATE TABLE IF NOT EXISTS person_sources(person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,relation TEXT NOT NULL DEFAULT 'GEDCOM',PRIMARY KEY(person_id,source_id,relation));
CREATE TABLE IF NOT EXISTS event_sources(event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,relation TEXT NOT NULL DEFAULT 'GEDCOM',PRIMARY KEY(event_id,source_id,relation));
CREATE TABLE IF NOT EXISTS note_sources(note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,relation TEXT NOT NULL DEFAULT 'GEDCOM',PRIMARY KEY(note_id,source_id,relation));
CREATE TABLE IF NOT EXISTS family_sources(family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,relation TEXT NOT NULL DEFAULT 'GEDCOM',PRIMARY KEY(family_id,source_id,relation));
CREATE TABLE IF NOT EXISTS citations(
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    owner_scope TEXT NOT NULL,
    person_id INTEGER REFERENCES people(id) ON DELETE CASCADE,
    family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
    note_id INTEGER REFERENCES notes(id) ON DELETE CASCADE,
    gedcom_owner_xref TEXT,
    context_tag TEXT,
    context_path TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS discovery_fts USING fts5(kind UNINDEXED,object_id UNINDEXED,person_id UNINDEXED,title,body);
"""
def _cols(db,t): return {r[1] for r in db.execute(f"PRAGMA table_info({t})")}
def migrate(db):
    if "gedcom_tag" not in _cols(db,"events"): db.execute("ALTER TABLE events ADD COLUMN gedcom_tag TEXT")
    for col,decl in (("marriage_date","TEXT"),("marriage_place","TEXT")):
        if col not in _cols(db,"families"): db.execute(f"ALTER TABLE families ADD COLUMN {col} {decl}")
    for col,decl in (("attachment_scope","TEXT"),("attachment_label","TEXT"),("is_preferred","INTEGER NOT NULL DEFAULT 0")):
        if col not in _cols(db,"media"): db.execute(f"ALTER TABLE media ADD COLUMN {col} {decl}")
    nc=_cols(db,"notes")
    for col,decl in (("gedcom_tag","TEXT"),("gedcom_note_xref","TEXT"),("is_referenced","INTEGER NOT NULL DEFAULT 0")):
        if col not in nc: db.execute(f"ALTER TABLE notes ADD COLUMN {col} {decl}")
    sc=_cols(db,"sources")
    for col,decl in (("source_type","TEXT"),("display_text","TEXT")):
        if col not in sc: db.execute(f"ALTER TABLE sources ADD COLUMN {col} {decl}")
    db.execute("CREATE TABLE IF NOT EXISTS event_sources(event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,relation TEXT NOT NULL DEFAULT 'GEDCOM',PRIMARY KEY(event_id,source_id,relation))")
    db.execute("CREATE TABLE IF NOT EXISTS note_sources(note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,relation TEXT NOT NULL DEFAULT 'GEDCOM',PRIMARY KEY(note_id,source_id,relation))")
    db.execute("CREATE TABLE IF NOT EXISTS family_sources(family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,relation TEXT NOT NULL DEFAULT 'GEDCOM',PRIMARY KEY(family_id,source_id,relation))")
    db.execute("""CREATE TABLE IF NOT EXISTS citations(id INTEGER PRIMARY KEY,source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,owner_scope TEXT NOT NULL,person_id INTEGER REFERENCES people(id) ON DELETE CASCADE,family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,note_id INTEGER REFERENCES notes(id) ON DELETE CASCADE,gedcom_owner_xref TEXT,context_tag TEXT,context_path TEXT)""")
    
    from .family_files import ensure_family_files
    ensure_family_files(db)
    from .external_evidence import ensure_external_evidence
    ensure_external_evidence(db)
    db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version',?)",(str(SCHEMA_VERSION),));db.commit()
def connect(path):
    p=Path(path).expanduser();p.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(p);db.row_factory=sqlite3.Row;db.executescript(SCHEMA);migrate(db);return db
def reset_imported_data(db):
    for t in ("discovery_fts","citations","family_sources","note_sources","event_sources","person_sources","sources","family_media","event_media","person_media","media","family_members","families","notes","events","people","imports"):
        db.execute(f"DELETE FROM {t}")
    db.commit()
