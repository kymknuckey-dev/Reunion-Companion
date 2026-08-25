from datetime import datetime, timedelta, timezone

from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence_scan import SourceBusyError
from reunion_companion.companion.ryerson_surname_bootstrap import (
    _surname_form_javascript,
    enqueue_unique_surnames,
    location_learning,
    run_one_surname,
    surname_queue_summary,
)

NOW=datetime(2026,8,25,5,0,0,tzinfo=timezone.utc)

def person(db,pid,xref,given,surname):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,xref,pid,given,surname,f"{given} {surname}","M",f"{given} /{surname}/"),
    )

def test_unique_surnames_are_queued_once(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Peter","Rigg")
    person(db,2,"@I2@","Other","Rigg")
    person(db,3,"@I3@","Rodney","Howie")
    db.commit()
    assert enqueue_unique_surnames(db)==2
    assert enqueue_unique_surnames(db)==0
    summary=surname_queue_summary(db)
    assert summary["total"]==2
    assert summary["queued"]==2

def test_surname_form_clears_other_primary_fields():
    js=_surname_form_javascript("Rigg")
    assert '[name="search_sn"]' in js
    assert '[name="search_gn"]' in js
    assert '[name="search_lo"]' in js
    assert '[name="search_y1"]' in js
    assert '[name="search_y2"]' in js
    assert '"Rigg"' in js

def test_busy_surname_retries_later(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Peter","Rigg")
    db.commit()
    enqueue_unique_surnames(db)

    def busy(db,surname):
        raise SourceBusyError("Ryerson server overloaded; retry later")

    result=run_one_surname(db,now=NOW,harvest_fn=busy)
    assert result["status"]=="retry_wait"
    row=db.execute("SELECT status,next_retry_at FROM companion_ryerson_surname_queue").fetchone()
    assert row["status"]=="retry_wait"
    assert row["next_retry_at"] is not None

def test_successful_surname_marks_completed(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Peter","Rigg")
    db.commit()
    enqueue_unique_surnames(db)

    from reunion_companion.companion.ryerson_harvest import cache_harvest_rows

    def harvest(db,surname):
        rows=[]
        for i in range(4):
            rows.append({
                "evidence_type":"death_notice",
                "source_record_name":f"Person {i} RIGG",
                "event_type":"Death",
                "event_date":f"0{i+1}JAN2000",
                "publication":"Test Paper",
                "publication_date":f"0{i+1}JAN2000",
                "details":None,
                "birth_date_claim":None,
                "place_claim":None,
            })
        cache_harvest_rows(
            db,
            rows,
            harvest_kind="surname",
            harvest_value=surname,
            harvest_year=0,
            page_number=1,
        )
        return {
            "surname":surname,
            "pages":1,
            "rows":4,
            "inserted":4,
            "existing":0,
            "unique_cached":4,
            "truncated":False,
        }

    import reunion_companion.companion.ryerson_surname_bootstrap as mod
    monkeypatch.setattr(
        mod,
        "cross_match_surname",
        lambda db,surname:{"findings":2,"created_findings":2},
    )
    result=run_one_surname(db,now=NOW,harvest_fn=harvest)
    assert result["status"]=="completed"
    row=db.execute(
        "SELECT status,result_count,match_count FROM companion_ryerson_surname_queue"
    ).fetchone()
    assert row["status"]=="completed"
    assert row["result_count"]==4
    assert row["match_count"]==2

def test_location_learning_counts_reviewable_findings(tmp_path):
    db=connect(tmp_path/"x.db")
    db.execute(
        "INSERT INTO companion_external_evidence(person_gedcom_xref,source_name,evidence_type,place_claim,match_confidence) VALUES('@I1@','Ryerson','death_notice','Curramulka',90)"
    )
    db.execute(
        "INSERT INTO companion_external_evidence(person_gedcom_xref,source_name,evidence_type,place_claim,match_confidence) VALUES('@I2@','Ryerson','death_notice','Curramulka',80)"
    )
    db.execute(
        "INSERT INTO companion_external_evidence(person_gedcom_xref,source_name,evidence_type,place_claim,match_confidence) VALUES('@I3@','Ryerson','death_notice','Adelaide',70)"
    )
    db.commit()
    rows=location_learning(db)
    assert rows[0]=={"location":"Curramulka","count":2}
