from datetime import datetime, timezone

from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_harvest import cache_harvest_rows
from reunion_companion.companion.ryerson_surname_bootstrap import (
    _progress_can_finalize_locally,
    _save_progress,
    enqueue_unique_surnames,
    reconcile_cached_surnames,
    run_one_surname,
)

NOW=datetime(2026,8,26,0,0,0,tzinfo=timezone.utc)


def person(db,pid,xref,given,surname):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,xref,pid,given,surname,f"{given} {surname}","M",f"{given} /{surname}/"),
    )


def notice(name,date):
    return {
        "evidence_type":"death_notice",
        "source_record_name":name,
        "event_type":"Death",
        "event_date":date,
        "publication":"Test Paper",
        "publication_date":date,
        "details":None,
        "birth_date_claim":None,
        "place_claim":None,
    }


def seed_complete_cached_progress(db):
    person(db,1,"@I1@","Test","Shearer")
    db.commit()
    enqueue_unique_surnames(db)
    cache_harvest_rows(
        db,[notice("A SHEARER","01JAN2000")],
        harvest_kind="surname",harvest_value="Shearer",harvest_year=0,
    )
    _save_progress(
        db,"Shearer",
        current_page=2,
        current_url="https://ryersonindex.org/search.php?page=2",
        pages_completed=2,
        rows_seen=1,
        inserted_rows=1,
        existing_rows=0,
        is_complete=False,
    )


def test_complete_cached_progress_is_locally_finalisable(tmp_path):
    db=connect(tmp_path/"x.db")
    seed_complete_cached_progress(db)
    assert _progress_can_finalize_locally(db,"Shearer") is True


def test_run_one_surname_finalises_without_hitting_ryerson(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.db")
    seed_complete_cached_progress(db)

    import reunion_companion.companion.ryerson_surname_bootstrap as mod
    monkeypatch.setattr(
        mod,"cross_match_surname",
        lambda db,surname:{"findings":0,"created_findings":0},
    )

    calls=[]
    def must_not_run(db,surname):
        calls.append(surname)
        raise AssertionError("Ryerson harvester must not be called")

    result=run_one_surname(db,now=NOW,harvest_fn=must_not_run)
    assert result["status"]=="completed"
    assert result["finalized_locally"] is True
    assert calls==[]

    q=db.execute(
        "SELECT status,result_count FROM companion_ryerson_surname_queue WHERE surname_key='shearer'"
    ).fetchone()
    p=db.execute(
        "SELECT is_complete FROM companion_ryerson_surname_progress WHERE surname_key='shearer'"
    ).fetchone()
    assert q["status"]=="completed"
    assert q["result_count"]==1
    assert p["is_complete"]==1


def test_reconcile_can_finalise_complete_cached_progress(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.db")
    seed_complete_cached_progress(db)

    import reunion_companion.companion.ryerson_surname_bootstrap as mod
    monkeypatch.setattr(
        mod,"cross_match_surname",
        lambda db,surname:{"findings":0,"created_findings":0},
    )

    assert reconcile_cached_surnames(db)==1
    q=db.execute(
        "SELECT status FROM companion_ryerson_surname_queue WHERE surname_key='shearer'"
    ).fetchone()
    assert q["status"]=="completed"


def test_partial_cache_is_not_finalised(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Test","Richards")
    db.commit()
    enqueue_unique_surnames(db)
    cache_harvest_rows(
        db,[notice("A RICHARDS","01JAN2000")],
        harvest_kind="surname",harvest_value="Richards",harvest_year=0,
    )
    _save_progress(
        db,"Richards",
        current_page=2,
        current_url="https://ryersonindex.org/search.php?page=2",
        pages_completed=1,
        rows_seen=2,
        inserted_rows=1,
        existing_rows=0,
        is_complete=False,
    )
    assert _progress_can_finalize_locally(db,"Richards") is False
