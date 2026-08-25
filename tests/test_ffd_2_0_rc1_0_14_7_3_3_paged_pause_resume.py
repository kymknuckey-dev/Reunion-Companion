from datetime import datetime, timezone

from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_surname_bootstrap import (
    BootstrapPaused,
    _save_progress,
    bootstrap_tick,
    pause_bootstrap,
    start_bootstrap,
    surname_progress,
)

NOW=datetime(2026,8,25,7,0,0,tzinfo=timezone.utc)

def person(db,pid,xref,given,surname):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,xref,pid,given,surname,f"{given} {surname}","M",f"{given} /{surname}/"),
    )

def test_progress_checkpoint_persists(tmp_path):
    db=connect(tmp_path/"x.db")
    _save_progress(
        db,"Mitchell",
        current_page=7,
        current_url="https://example.test/page7",
        pages_completed=6,
        rows_seen=600,
        inserted_rows=590,
        existing_rows=10,
        is_complete=False,
    )
    p=surname_progress(db,"Mitchell")
    assert p["current_page"]==7
    assert p["pages_completed"]==6
    assert p["rows_seen"]==600
    assert p["is_complete"]==0

def test_paused_harvest_does_not_complete_queue(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Test","Mitchell")
    db.commit()
    start_bootstrap(db)

    def paused_harvest(db,surname):
        raise BootstrapPaused("paused")

    import reunion_companion.companion.ryerson_surname_bootstrap as mod
    monkeypatch.setattr(
        mod,
        "cross_match_surname",
        lambda *a,**k: (_ for _ in ()).throw(AssertionError("must not match")),
    )

    result=bootstrap_tick(db,now=NOW,harvest_fn=paused_harvest)
    assert result["status"]=="paused"
    row=db.execute(
        "SELECT status,completed_at FROM companion_ryerson_surname_queue"
    ).fetchone()
    assert row["status"]=="queued"
    assert row["completed_at"] is None

def test_incomplete_harvest_does_not_complete_queue(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Test","Mitchell")
    db.commit()
    start_bootstrap(db)

    from reunion_companion.companion.ryerson_harvest import cache_harvest_rows

    cached_notice={
        "evidence_type":"death_notice",
        "source_record_name":"Test MITCHELL",
        "event_type":"Death",
        "event_date":"01JAN2000",
        "publication":"Test Paper",
        "publication_date":"02JAN2000",
        "details":None,
        "birth_date_claim":None,
        "place_claim":None,
    }
    cache_harvest_rows(
        db,[cached_notice],
        harvest_kind="surname",
        harvest_value="Mitchell",
        harvest_year=0,
        page_number=1,
    )

    def partial(db,surname):
        return {
            "surname":surname,
            "pages":20,
            "rows":2000,
            "inserted":999,
            "existing":1001,
            "unique_cached":1,
            "truncated":True,
            "paused":False,
        }

    import reunion_companion.companion.ryerson_surname_bootstrap as mod
    monkeypatch.setattr(
        mod,
        "cross_match_surname",
        lambda *a,**k: (_ for _ in ()).throw(AssertionError("must not match")),
    )

    result=bootstrap_tick(db,now=NOW,harvest_fn=partial)
    assert result["status"]=="incomplete"
    row=db.execute(
        "SELECT status,result_count,completed_at FROM companion_ryerson_surname_queue"
    ).fetchone()
    assert row["status"]=="queued"
    assert row["result_count"]==1
    assert row["completed_at"] is None
