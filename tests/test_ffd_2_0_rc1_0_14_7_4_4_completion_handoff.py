from datetime import datetime, timezone

from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_targeted_bootstrap import (
    populate_targeted_queue,
    run_selected_targeted_search,
)

NOW=datetime(2026,8,26,0,0,0,tzinfo=timezone.utc)

def add_person(db,pid,surname,given):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,"
        "display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,f"@I{pid}@",pid,given,surname,f"{given} {surname}","U",f"{given} /{surname}/"),
    )

def test_selected_search_completes_its_queue_row(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Smith","John")
    add_person(db,2,"Smith","Mary")
    db.commit()
    populate_targeted_queue(db)

    import reunion_companion.companion.ryerson_targeted_bootstrap as mod

    def fake_live(db,descriptor):
        assert descriptor["search_key"]=="name:smith|john"
        return {
            "result_count":6412,
            "match_count":12,
            "harvest":{"pages":7,"truncated":False},
        }

    monkeypatch.setattr(mod,"live_targeted_search",fake_live)

    result=run_selected_targeted_search(db,"name:smith|john",now=NOW)
    assert result["status"]=="completed"
    assert result["result_count"]==6412
    assert result["match_count"]==12

    john=db.execute(
        "SELECT status,attempts,result_count,match_count,last_attempt_at,completed_at "
        "FROM companion_ryerson_targeted_queue WHERE search_key='name:smith|john'"
    ).fetchone()
    mary=db.execute(
        "SELECT status,attempts FROM companion_ryerson_targeted_queue "
        "WHERE search_key='name:smith|mary'"
    ).fetchone()

    assert john["status"]=="completed"
    assert john["attempts"]==1
    assert john["result_count"]==6412
    assert john["match_count"]==12
    assert john["last_attempt_at"]==NOW.isoformat()
    assert john["completed_at"]==NOW.isoformat()
    assert mary["status"]=="queued"
    assert mary["attempts"]==0

def test_selected_search_missing_key_still_fails_cleanly(tmp_path):
    db=connect(tmp_path/"x.db")
    try:
        run_selected_targeted_search(db,"name:nope|nobody",now=NOW)
    except ValueError as exc:
        assert "not found" in str(exc).lower()
    else:
        raise AssertionError("expected ValueError")
