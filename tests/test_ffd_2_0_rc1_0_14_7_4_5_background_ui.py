import inspect

from reunion_companion.companion import beta_ui
from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_targeted_bootstrap import (
    start_targeted_bootstrap,
    targeted_status,
)

def add_person(db,pid,surname,given):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,"
        "display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,f"@I{pid}@",pid,given,surname,f"{given} {surname}","U",f"{given} /{surname}/"),
    )

def test_beta_ui_uses_targeted_bootstrap_routes_and_startup():
    source=inspect.getsource(beta_ui)
    assert "/research/ryerson/targeted/start" in source
    assert "/research/ryerson/targeted/pause" in source
    assert "start_targeted_bootstrap" in source
    assert "pause_targeted_bootstrap" in source
    assert "start_background_targeted_bootstrap" in source
    assert "live_targeted_search" in source
    startup=source[source.index("from .external_research_runner import start_background_runner"):]
    assert "start_background_surname_bootstrap" not in startup

def test_targeted_start_still_disables_old_surname_flag(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Smith","John")
    db.execute(
        "INSERT OR REPLACE INTO meta(key,value) "
        "VALUES('ryerson_surname_bootstrap_enabled','1')"
    )
    db.commit()
    result=start_targeted_bootstrap(db)
    old=db.execute(
        "SELECT value FROM meta WHERE key='ryerson_surname_bootstrap_enabled'"
    ).fetchone()["value"]
    assert result["enabled"] is True
    assert old=="0"

def test_targeted_status_has_ui_counts(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Smith","John")
    add_person(db,2,"Smith","Mary")
    db.commit()
    start_targeted_bootstrap(db)
    status=targeted_status(db)
    assert status["total"]==2
    assert status["queued"]==2
    assert status["searching"]==0
    assert status["completed"]==0
    assert status["core_surnames"]==["Knuckey"]
