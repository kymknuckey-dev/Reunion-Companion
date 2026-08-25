from datetime import datetime, timedelta, timezone
from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence_scan import SourceBusyError, SourceSearchError
from reunion_companion.companion.ryerson_surname_bootstrap import (
    bootstrap_cooldown_until,bootstrap_status,bootstrap_tick,
    enqueue_unique_surnames,start_bootstrap
)

NOW=datetime(2026,8,25,8,0,0,tzinfo=timezone.utc)

def person(db,pid,xref,given,surname):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,xref,pid,given,surname,f"{given} {surname}","M",f"{given} /{surname}/"),
    )

def test_source_busy_sets_global_cooldown(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Test","Richards"); db.commit(); start_bootstrap(db)
    def busy(db,surname): raise SourceBusyError("Ryerson server overloaded; retry later")
    result=bootstrap_tick(db,now=NOW,harvest_fn=busy)
    assert result["status"]=="retry_wait"
    assert result["source_cooldown"] is True
    assert bootstrap_cooldown_until(db)>NOW

def test_global_cooldown_blocks_other_surnames(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Test","Richards"); person(db,2,"@I2@","Other","Martin")
    db.commit(); start_bootstrap(db)
    def busy(db,surname): raise SourceBusyError("Ryerson server overloaded; retry later")
    bootstrap_tick(db,now=NOW,harvest_fn=busy)
    calls=[]
    def should_not_run(db,surname): calls.append(surname); return {}
    result=bootstrap_tick(db,now=NOW+timedelta(seconds=10),harvest_fn=should_not_run)
    assert result["status"]=="source_wait"
    assert calls==[]

def test_submit_field_not_found_is_transient_retry(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Test","Martin"); db.commit(); start_bootstrap(db)
    def bad_form(db,surname): raise SourceSearchError("submit field not found")
    result=bootstrap_tick(db,now=NOW,harvest_fn=bad_form)
    assert result["status"]=="retry_wait"
    row=db.execute("SELECT status,next_retry_at FROM companion_ryerson_surname_queue").fetchone()
    assert row["status"]=="retry_wait"
    assert row["next_retry_at"] is not None

def test_existing_failed_martin_is_recovered_on_start(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Test","Martin"); db.commit(); enqueue_unique_surnames(db)
    db.execute(
        "UPDATE companion_ryerson_surname_queue SET status='failed',attempts=1,last_error='submit field not found' WHERE surname_key='martin'"
    ); db.commit()
    result=start_bootstrap(db)
    assert result["recovered_transient"]==1
    row=db.execute("SELECT status,attempts,last_error FROM companion_ryerson_surname_queue WHERE surname_key='martin'").fetchone()
    assert row["status"]=="queued"
    assert row["attempts"]==0
    assert row["last_error"] is None

def test_status_exposes_cooldown(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Test","Richards"); db.commit(); start_bootstrap(db)
    def busy(db,surname): raise SourceBusyError("Ryerson server overloaded; retry later")
    bootstrap_tick(db,now=NOW,harvest_fn=busy)
    status=bootstrap_status(db)
    assert status["cooldown_until"] is not None
