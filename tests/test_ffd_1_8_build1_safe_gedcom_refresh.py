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


def test_successful_refresh_reconciles_external_discovery_state(tmp_path):
    from reunion_companion.companion.ryerson_discovery_review import (
        remember_discovery,
        set_discovery_state,
    )

    dbp = tmp_path / "companion.sqlite3"

    first = tmp_path / "first-discovery.ged"
    first.write_text(
        """0 HEAD
1 SOUR Reunion
0 @I1@ INDI
1 NAME John /Smith/
1 SEX M
1 BIRT
2 DATE 1 JAN 1950
0 @I2@ INDI
1 NAME Peter /Rigg/
1 SEX M
1 BIRT
2 DATE 21 MAY 1944
0 TRLR
"""
    )

    db = connect(dbp)
    import_gedcom(db, first)

    john = db.execute(
        "SELECT id FROM people WHERE gedcom_xref='@I1@'"
    ).fetchone()["id"]
    peter = db.execute(
        "SELECT id FROM people WHERE gedcom_xref='@I2@'"
    ).fetchone()["id"]

    stale = remember_discovery(
        db,
        person_id=john,
        source_name="Ryerson",
        external_record_key="notice:stale-after-refresh",
        proposed_fact_key="death:2021-01-01",
    )

    accepted = remember_discovery(
        db,
        person_id=peter,
        source_name="Ryerson",
        external_record_key="notice:accepted-after-refresh",
        proposed_fact_key="death:2021-01-02",
    )
    set_discovery_state(
        db,
        accepted["id"],
        "waiting_for_reunion",
        note="Accepted; add death date to Reunion",
    )
    db.close()

    second = tmp_path / "second-discovery.ged"
    second.write_text(
        """0 HEAD
1 SOUR Reunion
0 @I1@ INDI
1 NAME John /Smith/
1 SEX M
0 @I2@ INDI
1 NAME Peter /Rigg/
1 SEX M
1 BIRT
2 DATE 21 MAY 1944
1 DEAT
2 DATE 2 JAN 2021
0 TRLR
"""
    )

    result = safe_refresh(dbp, second)

    assert result["promoted"] is True
    assert result["discovery_reconciliation"]["retired_ineligible"] == 1
    assert result["discovery_reconciliation"]["confirmed_after_refresh"] == 1

    db = connect(dbp)
    try:
        stale_after = db.execute(
            """
            SELECT state,decision_note
            FROM companion_external_discovery_review
            WHERE id=?
            """,
            (stale["id"],),
        ).fetchone()

        accepted_after = db.execute(
            """
            SELECT state,decision_note,confirmed_at
            FROM companion_external_discovery_review
            WHERE id=?
            """,
            (accepted["id"],),
        ).fetchone()

        assert stale_after["state"] == "ineligible"
        assert (
            stale_after["decision_note"]
            == "Person no longer meets current external research eligibility rules"
        )

        assert accepted_after["state"] == "confirmed_complete"
        assert accepted_after["decision_note"] == "Accepted; add death date to Reunion"
        assert accepted_after["confirmed_at"] is not None
    finally:
        db.close()


def test_dry_run_does_not_reconcile_external_discovery_state(tmp_path):
    from reunion_companion.companion.ryerson_discovery_review import (
        remember_discovery,
    )

    dbp = tmp_path / "companion.sqlite3"

    first = tmp_path / "first-dry-discovery.ged"
    first.write_text(
        """0 HEAD
1 SOUR Reunion
0 @I1@ INDI
1 NAME John /Smith/
1 SEX M
1 BIRT
2 DATE 1 JAN 1950
0 TRLR
"""
    )

    db = connect(dbp)
    import_gedcom(db, first)

    john = db.execute(
        "SELECT id FROM people WHERE gedcom_xref='@I1@'"
    ).fetchone()["id"]

    row = remember_discovery(
        db,
        person_id=john,
        source_name="Ryerson",
        external_record_key="notice:dry-run",
        proposed_fact_key="death:2021-01-01",
    )
    db.close()

    second = tmp_path / "second-dry-discovery.ged"
    second.write_text(
        """0 HEAD
1 SOUR Reunion
0 @I1@ INDI
1 NAME John /Smith/
1 SEX M
0 TRLR
"""
    )

    result = safe_refresh(dbp, second, dry_run=True)

    assert result["promoted"] is False
    assert "discovery_reconciliation" not in result

    db = connect(dbp)
    try:
        after = db.execute(
            """
            SELECT state,decision_note
            FROM companion_external_discovery_review
            WHERE id=?
            """,
            (row["id"],),
        ).fetchone()

        assert after["state"] == "new"
        assert after["decision_note"] == ""
    finally:
        db.close()
