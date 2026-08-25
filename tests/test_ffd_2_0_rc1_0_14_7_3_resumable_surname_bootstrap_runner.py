from datetime import datetime, timezone
from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_harvest import cache_harvest_rows
from reunion_companion.companion.ryerson_surname_bootstrap import (
    bootstrap_enabled,bootstrap_status,bootstrap_tick,pause_bootstrap,start_bootstrap
)

NOW=datetime(2026,8,25,6,0,0,tzinfo=timezone.utc)

def person(db,pid,xref,given,surname):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
               (pid,xref,pid,given,surname,f"{given} {surname}","M",f"{given} /{surname}/"))

def test_start_bootstrap_populates_unique_surnames_and_persists(tmp_path):
    path=tmp_path/"x.db"; db=connect(path)
    person(db,1,"@I1@","Peter","Rigg"); person(db,2,"@I2@","Rodney","Howie"); db.commit()
    result=start_bootstrap(db)
    assert result["enabled"] is True
    assert result["newly_queued"]==2
    db.close()
    db=connect(path)
    assert bootstrap_enabled(db) is True
    assert bootstrap_status(db)["total"]==2

def test_pause_bootstrap_persists(tmp_path):
    path=tmp_path/"x.db"; db=connect(path)
    person(db,1,"@I1@","Peter","Rigg"); db.commit(); start_bootstrap(db); pause_bootstrap(db); db.close()
    db=connect(path); assert bootstrap_enabled(db) is False

def test_cached_direct_harvest_is_reconciled_without_live_search(tmp_path):
    db=connect(tmp_path/"x.db"); person(db,1,"@I1@","Peter","Rigg"); db.commit()
    row={"evidence_type":"death_notice","source_record_name":"Peter Stanley RIGG","event_type":"Death",
         "event_date":"02JAN2021","publication":"Adelaide Advertiser","publication_date":"04JAN2021",
         "details":"late of Curramulka","birth_date_claim":"21 May 1944","place_claim":"Curramulka"}
    cache_harvest_rows(db,[row],harvest_kind="surname",harvest_value="Rigg",harvest_year=0)
    result=start_bootstrap(db)
    assert result["reconciled_cached"]==1
    status=bootstrap_status(db)
    assert status["completed"]==1 and status["queued"]==0

def test_bootstrap_tick_processes_one_surname(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Peter","Rigg"); person(db,2,"@I2@","Rodney","Howie"); db.commit(); start_bootstrap(db)
    import reunion_companion.companion.ryerson_surname_bootstrap as mod
    monkeypatch.setattr(mod,"cross_match_surname",lambda db,surname:{"findings":0,"created_findings":0})
    calls=[]
    def fake_harvest(db,surname):
        calls.append(surname)
        return {"surname":surname,"pages":1,"rows":0,"inserted":0,"existing":0,"truncated":False}
    result=bootstrap_tick(db,now=NOW,harvest_fn=fake_harvest)
    assert result["status"]=="completed"
    assert len(calls)==1
    status=bootstrap_status(db)
    assert status["completed"]==1 and status["queued"]==1

def test_paused_bootstrap_tick_does_nothing(tmp_path):
    db=connect(tmp_path/"x.db"); person(db,1,"@I1@","Peter","Rigg"); db.commit(); start_bootstrap(db); pause_bootstrap(db)
    calls=[]
    def fake_harvest(db,surname):
        calls.append(surname); return {}
    result=bootstrap_tick(db,now=NOW,harvest_fn=fake_harvest)
    assert result["status"]=="paused"
    assert calls==[]
