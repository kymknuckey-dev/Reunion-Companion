from datetime import datetime, timedelta, timezone

from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence import external_evidence_for_person
from reunion_companion.companion.external_evidence_scan import (
    SourceBusyError,
    backoff_seconds,
    enqueue_death_research_candidates,
    next_runnable_scan,
    queue_rows,
    run_one_scan,
    scan_summary,
)

NOW=datetime(2026,8,25,0,0,0,tzinfo=timezone.utc)

def person(db,pid,xref,given,surname,display=None):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,"
        "display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,xref,pid,given,surname,display or f"{given} {surname}",
         "M",f"{given} /{surname}/"),
    )

def event(db,pid,kind,date=None,place=None,note=None):
    return db.execute(
        "INSERT INTO events(person_id,event_type,date_text,place_text,note_text) "
        "VALUES(?,?,?,?,?)",
        (pid,kind,date,place,note),
    ).lastrowid

def test_queue_is_persistent_and_deduplicated(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Peter Stanly","Rigg")
    event(db,1,"Birth","21 May 1944","Brighton Community Hospital")
    db.commit()
    assert enqueue_death_research_candidates(db)==1
    assert enqueue_death_research_candidates(db)==0
    rows=queue_rows(db)
    assert len(rows)==1
    assert rows[0]["status"]=="queued"
    assert rows[0]["person_gedcom_xref"]=="@I1@"

def test_server_busy_becomes_retry_wait_not_no_match(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Peter Stanly","Rigg")
    db.commit()
    enqueue_death_research_candidates(db)
    def busy(profile):
        raise SourceBusyError("Server busy; try again later")
    result=run_one_scan(db,busy,now=NOW)
    assert result["status"]=="retry_wait"
    row=queue_rows(db)[0]
    assert row["status"]=="retry_wait"
    assert row["attempts"]==1
    assert "busy" in row["last_error"].lower()
    assert row["completed_at"] is None
    assert next_runnable_scan(db,now=NOW) is None
    assert next_runnable_scan(db,now=NOW+timedelta(minutes=5)) is not None

def test_backoff_increases_and_is_capped():
    assert backoff_seconds(1)==300
    assert backoff_seconds(2)==600
    assert backoff_seconds(3)==1200
    assert backoff_seconds(20)==21600

def test_successful_no_result_is_distinct_from_busy(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Nobody","Example")
    db.commit()
    enqueue_death_research_candidates(db)
    result=run_one_scan(db,lambda profile: [],now=NOW)
    assert result["status"]=="succeeded_no_match"
    row=queue_rows(db)[0]
    assert row["status"]=="succeeded_no_match"
    assert row["completed_at"] is not None

def test_peter_candidate_is_matched_and_persisted(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Peter Stanly","Rigg","Peter Stanly Rigg")
    event(db,1,"Birth","21 May 1944","Brighton Community Hospital")
    db.commit()
    enqueue_death_research_candidates(db)
    def search(profile):
        assert profile["display_name"]=="Peter Stanly Rigg"
        return [{
            "evidence_type":"death_notice",
            "source_record_name":"Peter Stanley Rigg",
            "event_type":"Death",
            "event_date":"02JAN2021",
            "publication":"Adelaide Advertiser",
            "publication_date":"04JAN2021",
            "details":"late of Curramulka (born 21 May 1944)",
            "birth_date_claim":"21 May 1944",
            "place_claim":"Curramulka",
        }]
    result=run_one_scan(db,search,now=NOW)
    assert result["status"]=="succeeded_with_findings"
    assert result["result_count"]==1
    findings=external_evidence_for_person(db,"@I1@")
    assert len(findings)==1
    assert findings[0]["source_name"]=="Ryerson"
    assert findings[0]["source_record_name"]=="Peter Stanley Rigg"
    assert findings[0]["match_confidence"]>=80

def test_rejected_candidate_is_not_stored(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","John","Smith")
    event(db,1,"Birth","01 Jan 1940","Adelaide")
    db.commit()
    enqueue_death_research_candidates(db)
    result=run_one_scan(
        db,
        lambda profile: [{
            "source_record_name":"John Smith",
            "birth_date_claim":"01 Jan 1955",
            "evidence_type":"death_notice",
            "event_type":"Death",
        }],
        now=NOW,
    )
    assert result["status"]=="succeeded_no_match"
    assert external_evidence_for_person(db,"@I1@")==[]

def test_summary_preserves_checkpoint_states(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Alpha","One")
    person(db,2,"@I2@","Beta","Two")
    db.commit()
    enqueue_death_research_candidates(db)
    run_one_scan(db,lambda profile: [],now=NOW)
    summary=scan_summary(db)
    assert summary["total"]==2
    assert summary["counts"]["succeeded_no_match"]==1
    assert summary["counts"]["queued"]==1
