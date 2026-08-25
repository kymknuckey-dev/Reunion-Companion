from datetime import datetime, timedelta, timezone

from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence_scan import SourceBusyError
from reunion_companion.companion.external_research_runner import runner_tick,runner_status,source_waiting,start_runner

NOW=datetime(2026,8,25,2,0,0,tzinfo=timezone.utc)

def person(db,pid,xref,given,surname):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
               (pid,xref,pid,given,surname,f"{given} {surname}","M",f"{given} /{surname}/"))

def test_busy_response_cools_down_whole_source(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Alpha","One"); person(db,2,"@I2@","Beta","Two"); db.commit(); start_runner(db)
    def busy(profile): raise SourceBusyError("Server overloaded")
    first=runner_tick(db,busy,now=NOW)
    assert first["status"]=="retry_wait"
    assert source_waiting(db,NOW+timedelta(minutes=1))
    calls=[]
    second=runner_tick(db,lambda p:calls.append(p),now=NOW+timedelta(minutes=1))
    assert second["status"]=="source_wait"
    assert calls==[]

def test_source_resumes_after_cooldown(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Alpha","One"); person(db,2,"@I2@","Beta","Two"); db.commit(); start_runner(db)
    def busy(profile): raise SourceBusyError("Server overloaded")
    runner_tick(db,busy,now=NOW)
    calls=[]
    result=runner_tick(db,lambda p:calls.append(p["display_name"]) or [],now=NOW+timedelta(minutes=6))
    assert result["status"]=="succeeded_no_match"
    assert len(calls)==1

def test_runner_status_exposes_cooldown(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Peter","Rigg"); db.commit(); start_runner(db)
    def busy(profile): raise SourceBusyError("Server overloaded")
    runner_tick(db,busy,now=NOW)
    assert runner_status(db)["cooldown_until"] is not None
