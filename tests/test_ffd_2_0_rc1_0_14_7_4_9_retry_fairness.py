from datetime import datetime, timezone

from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence_scan import SourceBusyError, SourceSearchError
from reunion_companion.companion.ryerson_targeted_bootstrap import (
    populate_targeted_queue,
    run_one_targeted,
    targeted_search_retry_exhausted,
)

NOW=datetime(2026,8,26,0,0,0,tzinfo=timezone.utc)


def add_person(db,pid,surname,given):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,"
        "display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,f"@I{pid}@",pid,given,surname,f"{given} {surname}","U",f"{given} /{surname}/"),
    )


def enable(db):
    db.execute(
        "INSERT OR REPLACE INTO meta(key,value) "
        "VALUES('ryerson_targeted_bootstrap_enabled','1')"
    )
    db.commit()


def test_search_retry_exhaustion_boundary():
    assert targeted_search_retry_exhausted(1) is False
    assert targeted_search_retry_exhausted(2) is False
    assert targeted_search_retry_exhausted(3) is True
    assert targeted_search_retry_exhausted(20) is True


def test_non_overload_search_timeout_fails_after_three_attempts(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Viney","Matthew")
    db.commit()
    populate_targeted_queue(db)
    enable(db)

    def timeout(db,descriptor):
        raise SourceSearchError(
            "Timed out waiting for verified Ryerson surname results for Viney; "
            "last parsed row count=0"
        )

    r1=run_one_targeted(db,now=NOW,search_fn=timeout)
    assert r1["status"]=="retry_wait"
    db.execute(
        "UPDATE companion_ryerson_targeted_queue SET next_retry_at=NULL "
        "WHERE search_key='name:viney|matthew'"
    )
    db.commit()

    r2=run_one_targeted(db,now=NOW,search_fn=timeout)
    assert r2["status"]=="retry_wait"
    db.execute(
        "UPDATE companion_ryerson_targeted_queue SET next_retry_at=NULL "
        "WHERE search_key='name:viney|matthew'"
    )
    db.commit()

    r3=run_one_targeted(db,now=NOW,search_fn=timeout)
    assert r3["status"]=="failed"
    assert r3["retry_exhausted"] is True

    row=db.execute(
        "SELECT status,attempts,last_error,next_retry_at "
        "FROM companion_ryerson_targeted_queue "
        "WHERE search_key='name:viney|matthew'"
    ).fetchone()
    assert row["status"]=="failed"
    assert row["attempts"]==3
    assert "Timed out waiting" in row["last_error"]
    assert row["next_retry_at"] is None


def test_exhausted_bad_query_does_not_starve_fresh_queue(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Viney","Matthew")
    add_person(db,2,"Smith","Mary")
    db.commit()
    populate_targeted_queue(db)
    enable(db)

    db.execute(
        "UPDATE companion_ryerson_targeted_queue "
        "SET attempts=2,status='retry_wait',next_retry_at=NULL "
        "WHERE search_key='name:viney|matthew'"
    )
    db.commit()

    calls=[]
    def search(db,descriptor):
        calls.append(descriptor["search_key"])
        if descriptor["search_key"]=="name:viney|matthew":
            raise SourceSearchError("verification timeout")
        return {"result_count":5,"match_count":1}

    first=run_one_targeted(db,now=NOW,search_fn=search)
    assert first["status"]=="failed"

    second=run_one_targeted(db,now=NOW,search_fn=search)
    assert second["status"]=="completed"
    assert second["search_key"]=="name:smith|mary"
    assert calls==["name:viney|matthew","name:smith|mary"]


def test_explicit_overload_is_not_failed_at_three_attempts(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Brown","John")
    db.commit()
    populate_targeted_queue(db)
    enable(db)

    db.execute(
        "UPDATE companion_ryerson_targeted_queue SET attempts=2 "
        "WHERE search_key='name:brown|john'"
    )
    db.commit()

    def busy(db,descriptor):
        raise SourceBusyError("Ryerson server overloaded; retry later")

    result=run_one_targeted(db,now=NOW,search_fn=busy)
    assert result["status"]=="retry_wait"

    row=db.execute(
        "SELECT status,attempts,next_retry_at "
        "FROM companion_ryerson_targeted_queue "
        "WHERE search_key='name:brown|john'"
    ).fetchone()
    assert row["status"]=="retry_wait"
    assert row["attempts"]==3
    assert row["next_retry_at"] is not None
