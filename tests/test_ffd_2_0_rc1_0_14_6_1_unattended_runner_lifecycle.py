from reunion_companion.companion.database import connect
from reunion_companion.companion.external_research_runner import start_runner,pause_runner,runner_enabled,runner_status,runner_tick
from reunion_companion.companion.external_evidence_scan import SourceBusyError,queue_rows

def person(db,pid,xref,given,surname):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
               (pid,xref,pid,given,surname,f"{given} {surname}","M",f"{given} /{surname}/"))

def test_start_persists_and_queues(tmp_path):
    path=tmp_path/"x.db"; db=connect(path); person(db,1,"@I1@","Peter","Rigg"); db.commit()
    r=start_runner(db); assert r["enabled"] and r["newly_queued"]==1; db.close()
    db=connect(path); assert runner_enabled(db); assert len(queue_rows(db))==1

def test_pause_persists(tmp_path):
    path=tmp_path/"x.db"; db=connect(path); person(db,1,"@I1@","Peter","Rigg"); db.commit(); start_runner(db)
    assert pause_runner(db)["enabled"] is False; db.close(); db=connect(path); assert not runner_enabled(db)

def test_paused_tick_does_not_call_transport(tmp_path):
    db=connect(tmp_path/"x.db"); calls=[]; assert runner_tick(db,lambda p:calls.append(p))["status"]=="paused"; assert calls==[]

def test_enabled_tick_processes_one(tmp_path):
    db=connect(tmp_path/"x.db"); person(db,1,"@I1@","Alpha","One"); person(db,2,"@I2@","Beta","Two"); db.commit(); start_runner(db)
    calls=[]; r=runner_tick(db,lambda p:calls.append(p["display_name"]) or [])
    assert r["status"]=="succeeded_no_match" and len(calls)==1
    st=runner_status(db); assert st["no_match"]==1 and st["queued"]==1

def test_busy_waits_without_disabling_runner(tmp_path):
    db=connect(tmp_path/"x.db"); person(db,1,"@I1@","Peter","Rigg"); db.commit(); start_runner(db)
    def busy(profile): raise SourceBusyError("server busy")
    r=runner_tick(db,busy); assert r["status"]=="retry_wait"; assert runner_enabled(db); assert runner_status(db)["retry_wait"]==1
