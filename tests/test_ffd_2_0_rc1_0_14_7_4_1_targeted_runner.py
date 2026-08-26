from datetime import datetime, timedelta, timezone

from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence_scan import SourceBusyError
from reunion_companion.companion.ryerson_targeted_bootstrap import (
    run_one_targeted,start_targeted_bootstrap,targeted_form_javascript,
    targeted_overload_backoff_seconds,targeted_source_waiting
)

NOW=datetime(2026,8,26,0,0,0,tzinfo=timezone.utc)

def add_person(db,pid,surname,given):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,"
        "display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,f"@I{pid}@",pid,given,surname,f"{given} {surname}","U",f"{given} /{surname}/"),
    )

def test_targeted_form_fills_surname_and_given_name():
    js=targeted_form_javascript("Smith","John")
    assert "search_sn" in js and "search_gn" in js
    assert '"Smith"' in js and '"John"' in js

def test_core_form_leaves_given_name_blank():
    js=targeted_form_javascript("Knuckey","")
    assert '"Knuckey"' in js
    assert '""' in js

def test_targeted_runner_passes_stable_descriptor(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Smith","John William")
    db.commit()
    start_targeted_bootstrap(db)
    seen=[]
    def search(db,descriptor):
        seen.append(descriptor)
        return {"result_count":7,"match_count":2}
    result=run_one_targeted(db,now=NOW,search_fn=search)
    assert result["status"]=="completed"
    assert seen[0]["search_key"]=="name:smith|john"
    assert seen[0]["harvest_kind"]=="surname_given"
    assert seen[0]["harvest_value"]=="Smith|John"

def test_core_runner_descriptor_is_broad_surname(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Knuckey","John")
    add_person(db,2,"Knuckey","Mary")
    db.commit()
    start_targeted_bootstrap(db)
    seen=[]
    def search(db,descriptor):
        seen.append(descriptor)
        return {"result_count":12,"match_count":3}
    result=run_one_targeted(db,now=NOW,search_fn=search)
    assert result["status"]=="completed"
    assert seen[0]["search_kind"]=="surname"
    assert seen[0]["given_name"]==""
    assert seen[0]["harvest_kind"]=="surname"

def test_targeted_overload_short_source_cooldown(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Smith","John")
    db.commit()
    start_targeted_bootstrap(db)
    def busy(db,descriptor):
        raise SourceBusyError("Ryerson server overloaded; retry later")
    result=run_one_targeted(db,now=NOW,search_fn=busy)
    assert result["status"]=="retry_wait"
    assert result["next_retry_at"]==(NOW+timedelta(seconds=30)).isoformat()
    assert targeted_source_waiting(db,NOW+timedelta(seconds=10)) is True
    assert targeted_source_waiting(db,NOW+timedelta(seconds=31)) is False

def test_targeted_overload_schedule_caps_at_five_minutes():
    assert targeted_overload_backoff_seconds(1)==30
    assert targeted_overload_backoff_seconds(2)==60
    assert targeted_overload_backoff_seconds(3)==120
    assert targeted_overload_backoff_seconds(4)==300
    assert targeted_overload_backoff_seconds(20)==300

def test_targeted_completion_persists_counts(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Smith","John")
    db.commit()
    start_targeted_bootstrap(db)
    def search(db,descriptor):
        return {"result_count":23,"match_count":4}
    run_one_targeted(db,now=NOW,search_fn=search)
    row=db.execute(
        "SELECT status,attempts,result_count,match_count "
        "FROM companion_ryerson_targeted_queue WHERE search_key='name:smith|john'"
    ).fetchone()
    assert row["status"]=="completed"
    assert row["attempts"]==1
    assert row["result_count"]==23
    assert row["match_count"]==4
