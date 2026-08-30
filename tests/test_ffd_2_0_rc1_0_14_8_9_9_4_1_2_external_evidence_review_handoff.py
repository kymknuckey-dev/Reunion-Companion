from reunion_companion.companion.database import connect
from reunion_companion.companion.external_research_runner import start_runner, runner_tick
from reunion_companion.companion.ryerson_discovery_review import discoveries_for_person
from reunion_companion.companion.external_evidence import add_external_evidence


def add_person(db,pid,xref,given,surname):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (pid,xref,pid,given,surname,f"{given} {surname}","F",f"{given} /{surname}/"),
    )
    db.execute("INSERT INTO events(person_id,event_type,date_text) VALUES(?,?,?)",(pid,"Birth","01 Jan 1940"))
    db.commit()


def test_successful_runner_scan_materialises_review_immediately(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"@I1@","Margaret Joan","Butler")
    start_runner(db)
    result=runner_tick(db,lambda profile:[{
        "source_record_name":"Margaret Joan BUTLER",
        "event_type":"Death",
        "event_date":"04JUL2007",
        "publication":"Adelaide Advertiser",
        "publication_date":"11JUL2007",
    }])
    assert result["status"]=="succeeded_with_findings"
    rows=discoveries_for_person(db,1)
    assert len(rows)==1
    assert rows[0]["state"]=="new"
    assert rows[0]["proposed_fact_key"]=="death:04JUL2007"


def test_start_runner_backfills_preexisting_new_findings(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"@I1@","Margaret Joan","Butler")
    add_external_evidence(
        db,
        person_gedcom_xref="@I1@",
        person_name_snapshot="Margaret Joan Butler",
        source_name="Ryerson",
        evidence_type="death_notice",
        source_record_name="Margaret Joan BUTLER",
        event_type="Death",
        event_date="04JUL2007",
        publication="Adelaide Advertiser",
        publication_date="11JUL2007",
        details=None,
        birth_date_claim=None,
        place_claim=None,
        match_confidence=75,
        match_reason="test",
        review_status="new",
    )
    assert discoveries_for_person(db,1)==[]
    start_runner(db)
    rows=discoveries_for_person(db,1)
    assert len(rows)==1
    assert rows[0]["state"]=="new"


def test_backfill_is_idempotent(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"@I1@","Margaret Joan","Butler")
    add_external_evidence(
        db, person_gedcom_xref="@I1@", person_name_snapshot="Margaret Joan Butler",
        source_name="Ryerson", evidence_type="death_notice", source_record_name="Margaret Joan BUTLER",
        event_type="Death", event_date="04JUL2007", publication="Adelaide Advertiser",
        publication_date="11JUL2007", details=None, birth_date_claim=None, place_claim=None,
        match_confidence=75, match_reason="test", review_status="new",
    )
    start_runner(db); start_runner(db)
    assert len(discoveries_for_person(db,1))==1
