from io import StringIO
from contextlib import redirect_stdout

from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_cli import main,recent_rows
from reunion_companion.companion.ryerson_targeted_bootstrap import (
    next_targeted_search,
    populate_targeted_queue,
)


def add_person(db,pid,surname,given):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,"
        "display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,f"@I{pid}@",pid,given,surname,f"{given} {surname}","U",f"{given} /{surname}/"),
    )


def test_name_searches_are_prioritised_before_broad_core_surname(tmp_path):
    db=connect(tmp_path/"x.db")
    for pid in range(1,6):
        add_person(db,pid,"Knuckey",f"Person{pid}")
    add_person(db,10,"Smith","John")
    db.commit()

    populate_targeted_queue(db)
    row=next_targeted_search(db)

    assert row["search_kind"]=="name"
    assert row["search_key"]=="name:smith|john"


def test_retry_wait_still_takes_precedence_over_new_name_search(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Smith","John")
    add_person(db,2,"Brown","Mary")
    db.commit()
    populate_targeted_queue(db)

    db.execute(
        """
        UPDATE companion_ryerson_targeted_queue
        SET status='retry_wait',next_retry_at=NULL
        WHERE search_key='name:brown|mary'
        """
    )
    db.commit()

    row=next_targeted_search(db)
    assert row["search_key"]=="name:brown|mary"


def test_cli_status_reports_normal_death_research_queue(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Smith","John")
    add_person(db,2,"Smith","Mary")
    db.commit()
    db.execute("INSERT INTO events(person_id,event_type,date_text,place_text,note_text) VALUES(1,\'Birth\',\'1 Jan 1950\',\'Adelaide\',\'\')")
    db.execute("INSERT INTO events(person_id,event_type,date_text,place_text,note_text) VALUES(2,\'Birth\',\'1 Jan 1950\',\'Adelaide\',\'\')")
    db.commit()
    from reunion_companion.companion.external_evidence_scan import enqueue_death_research_candidates
    enqueue_death_research_candidates(db)
    db.close()

    out=StringIO()
    with redirect_stdout(out):
        rc=main(["--db",str(tmp_path/"x.db"),"status"])

    text=out.getvalue()
    assert rc==0
    assert "total=2" in text
    assert "queued=2" in text
    assert "family_wide_enabled=False" in text


def test_cli_recent_reads_death_research_rows(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Smith","John")
    db.execute("INSERT INTO companion_external_scan_queue(source_name,person_gedcom_xref,person_name_snapshot,status,last_attempt_at,result_count) VALUES('Ryerson','@I1@','John Smith','succeeded_with_findings','2026-08-30T01:00:00+00:00',3)")
    db.commit()

    rows=recent_rows(db,10)
    assert len(rows)==1
    assert rows[0]["person_name_snapshot"]=="John Smith"
    assert rows[0]["result_count"]==3
