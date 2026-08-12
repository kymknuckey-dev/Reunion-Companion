from pathlib import Path
import sqlite3
import pytest

from reunion_companion.companion.database import connect
from reunion_companion.companion.gedcom import import_gedcom
from reunion_companion.companion.safe_refresh import safe_refresh, semantic_snapshot, validate_database


def ged(path: Path, name='John /Smith/', birth='1 JAN 1900', note='Original note', extra=''):
    path.write_text(f'''0 HEAD\n1 SOUR Reunion\n0 @I1@ INDI\n1 NAME {name}\n1 SEX M\n1 BIRT\n2 DATE {birth}\n2 PLAC Adelaide, South Australia\n1 NOTE {note}\n{extra}0 TRLR\n''')
    return path


def make_db(tmp_path):
    dbp=tmp_path/'companion.sqlite3'
    db=connect(dbp)
    import_gedcom(db,ged(tmp_path/'first.ged'))
    db.close()
    return dbp


def test_dry_run_detects_change_without_touching_working_db(tmp_path):
    dbp=make_db(tmp_path)
    before=dbp.read_bytes()
    second=ged(tmp_path/'second.ged',birth='2 JAN 1900')
    r=safe_refresh(dbp,second,dry_run=True)
    assert r['status']=='dry-run'
    assert r['changes']['people']['changed']==1
    assert r['changes']['events']['changed']==1
    assert r['promoted'] is False
    assert r['backup_path'] is None
    assert dbp.read_bytes()==before
    db=connect(dbp)
    try: assert db.execute("SELECT date_text FROM events WHERE event_type='Birth'").fetchone()[0]=='1 JAN 1900'
    finally: db.close()


def test_commit_rebuilds_data_creates_backup_and_promotes_atomically(tmp_path):
    dbp=make_db(tmp_path)
    second=ged(tmp_path/'second.ged',birth='2 JAN 1900',note='Corrected note')
    r=safe_refresh(dbp,second)
    assert r['promoted'] is True
    assert r['changes']['notes']['changed']==1
    backup=Path(r['backup_path'])
    assert backup.exists()
    db=connect(dbp)
    try:
        assert db.execute("SELECT date_text FROM events WHERE event_type='Birth'").fetchone()[0]=='2 JAN 1900'
        assert db.execute("SELECT text FROM notes").fetchone()[0]=='Corrected note'
        assert validate_database(db).ok
    finally: db.close()
    old=connect(backup)
    try: assert old.execute("SELECT date_text FROM events WHERE event_type='Birth'").fetchone()[0]=='1 JAN 1900'
    finally: old.close()


def test_invalid_gedcom_never_replaces_working_database(tmp_path):
    dbp=make_db(tmp_path)
    bad=tmp_path/'bad.ged'; bad.write_text('0 HEAD\n0 TRLR\n')
    with pytest.raises(ValueError): safe_refresh(dbp,bad)
    db=connect(dbp)
    try: assert db.execute("SELECT display_name FROM people").fetchone()[0]=='John Smith'
    finally: db.close()
    assert not (tmp_path/'backups').exists()


def test_removed_person_is_removed_not_left_stale(tmp_path):
    dbp=make_db(tmp_path)
    p=tmp_path/'two.ged'
    p.write_text('''0 HEAD\n0 @I1@ INDI\n1 NAME John /Smith/\n0 @I2@ INDI\n1 NAME Jane /Smith/\n0 TRLR\n''')
    safe_refresh(dbp,p)
    p2=tmp_path/'one.ged'
    p2.write_text('''0 HEAD\n0 @I1@ INDI\n1 NAME John /Smith/\n0 TRLR\n''')
    r=safe_refresh(dbp,p2)
    assert r['changes']['people']['removed']==1
    db=connect(dbp)
    try: assert db.execute('SELECT COUNT(*) FROM people').fetchone()[0]==1
    finally: db.close()


def test_companion_owned_tables_survive_refresh(tmp_path):
    dbp=make_db(tmp_path)
    db=connect(dbp)
    db.execute('CREATE TABLE IF NOT EXISTS local_demo_state(key TEXT PRIMARY KEY,value TEXT)')
    db.execute("INSERT INTO local_demo_state VALUES('keep','yes')")
    db.commit();db.close()
    safe_refresh(dbp,ged(tmp_path/'second.ged',birth='3 JAN 1900'))
    db=connect(dbp)
    try: assert db.execute("SELECT value FROM local_demo_state WHERE key='keep'").fetchone()[0]=='yes'
    finally: db.close()
