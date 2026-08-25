from datetime import datetime, timedelta, timezone

from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence_scan import SourceBusyError
from reunion_companion.companion.ryerson_surname_bootstrap import (
    bootstrap_cooldown_until,
    bootstrap_tick,
    ryerson_overload_backoff_seconds,
    start_bootstrap,
)

NOW=datetime(2026,8,26,0,0,0,tzinfo=timezone.utc)

def person(db,pid,xref,given,surname):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,xref,pid,given,surname,f"{given} {surname}","M",f"{given} /{surname}/"),
    )

def test_ryerson_overload_schedule():
    assert ryerson_overload_backoff_seconds(1)==30
    assert ryerson_overload_backoff_seconds(2)==60
    assert ryerson_overload_backoff_seconds(3)==120
    assert ryerson_overload_backoff_seconds(4)==300
    assert ryerson_overload_backoff_seconds(5)==300
    assert ryerson_overload_backoff_seconds(17)==300

def test_overload_sets_30_second_source_wait_on_first_attempt(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Test","Richards")
    db.commit()
    start_bootstrap(db)

    def busy(db,surname):
        raise SourceBusyError("Ryerson server overloaded; retry later")

    result=bootstrap_tick(db,now=NOW,harvest_fn=busy)
    assert result["status"]=="retry_wait"
    assert result["next_retry_at"]==(NOW+timedelta(seconds=30)).isoformat()
    assert bootstrap_cooldown_until(db)==NOW+timedelta(seconds=30)

def test_repeated_overload_caps_at_five_minutes(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Test","Richards")
    db.commit()
    start_bootstrap(db)

    db.execute(
        "UPDATE companion_ryerson_surname_queue "
        "SET attempts=16,status='queued',next_retry_at=NULL "
        "WHERE surname_key='richards'"
    )
    db.commit()

    def busy(db,surname):
        raise SourceBusyError("Ryerson server overloaded; retry later")

    result=bootstrap_tick(db,now=NOW,harvest_fn=busy)
    assert result["status"]=="retry_wait"
    assert result["next_retry_at"]==(NOW+timedelta(minutes=5)).isoformat()
    assert bootstrap_cooldown_until(db)==NOW+timedelta(minutes=5)

def test_source_wait_still_blocks_another_surname(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Test","Richards")
    person(db,2,"@I2@","Other","Martin")
    db.commit()
    start_bootstrap(db)

    def busy(db,surname):
        raise SourceBusyError("Ryerson server overloaded; retry later")

    bootstrap_tick(db,now=NOW,harvest_fn=busy)

    calls=[]
    def should_not_run(db,surname):
        calls.append(surname)
        return {}

    result=bootstrap_tick(
        db,
        now=NOW+timedelta(seconds=10),
        harvest_fn=should_not_run,
    )
    assert result["status"]=="source_wait"
    assert calls==[]
