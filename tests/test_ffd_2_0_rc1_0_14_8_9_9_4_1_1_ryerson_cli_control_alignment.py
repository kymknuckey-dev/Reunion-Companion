from datetime import datetime, timedelta, timezone

from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_cli import main, recent_rows
from reunion_companion.companion.external_research_runner import META_ENABLED
from reunion_companion.companion.ryerson_targeted_bootstrap import META_TARGETED_ENABLED as FAMILY_META_ENABLED


def add_eligible_person(db,pid=1,given="John",surname="Smith"):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (pid,f"@I{pid}@",pid,given,surname,f"{given} {surname}","U",f"{given} /{surname}/"),
    )
    db.execute(
        "INSERT INTO events(person_id,event_type,date_text,place_text,note_text) VALUES(?,?,?,?,?)",
        (pid,"Birth","1 Jan 1950","Adelaide",""),
    )
    db.commit()


def meta(db,key):
    row=db.execute("SELECT value FROM meta WHERE key=?",(key,)).fetchone()
    return row["value"] if row else None


def test_start_controls_death_research_and_keeps_family_wide_paused(tmp_path,capsys):
    path=tmp_path/"x.db"
    db=connect(path)
    add_eligible_person(db)
    db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",(FAMILY_META_ENABLED,"1"))
    db.commit(); db.close()

    assert main(["--db",str(path),"start"])==0
    db=connect(path)
    assert meta(db,META_ENABLED)=="1"
    assert meta(db,FAMILY_META_ENABLED)=="0"
    assert db.execute("SELECT COUNT(*) n FROM companion_external_scan_queue WHERE source_name='Ryerson'").fetchone()["n"]==1
    db.close()


def test_pause_controls_death_research_and_family_wide_stays_paused(tmp_path,capsys):
    path=tmp_path/"x.db"
    db=connect(path)
    db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",(META_ENABLED,"1"))
    db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",(FAMILY_META_ENABLED,"1"))
    db.commit(); db.close()

    assert main(["--db",str(path),"pause"])==0
    db=connect(path)
    assert meta(db,META_ENABLED)=="0"
    assert meta(db,FAMILY_META_ENABLED)=="0"
    db.close()


def test_status_reports_death_research_primary_and_family_wide_separately(tmp_path,capsys):
    path=tmp_path/"x.db"
    db=connect(path); add_eligible_person(db); db.close()
    main(["--db",str(path),"populate"]); capsys.readouterr()
    main(["--db",str(path),"status"])
    out=capsys.readouterr().out
    assert "total=1 queued=1" in out
    assert "findings=0 no_finding=0" in out
    assert "family_wide_enabled=False" in out


def test_recent_reads_death_research_not_family_wide(tmp_path):
    path=tmp_path/"x.db"
    db=connect(path); add_eligible_person(db)
    db.execute(
        "INSERT INTO companion_external_scan_queue(source_name,person_gedcom_xref,person_name_snapshot,status,last_attempt_at) "
        "VALUES('Ryerson','@I1@','John Smith','succeeded_no_match',?)",
        ((datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat(),),
    )
    db.commit()
    rows=recent_rows(db,10)
    assert len(rows)==1
    assert rows[0]["person_name_snapshot"]=="John Smith"
    assert rows[0]["status"]=="succeeded_no_match"
    db.close()
