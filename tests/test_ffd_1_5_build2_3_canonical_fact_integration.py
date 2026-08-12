from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question,_event_rows
from reunion_companion.companion.timeline_engine import timeline_for_person

def seed(db):
 ps=[
 (1,'@I1@',1,'Kym Wayne','Knuckey','Kym Wayne Knuckey','M','Kym Wayne /Knuckey/'),
 (2,'@I2@',2,'Barry George','Jones','Barry George Jones','M','Barry George /Jones/')]
 db.executemany("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",ps)
 db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(1,1,'Occupation',NULL,NULL,'Intranet Control Administrator [ Santos Ltd. ]',NULL,'OCCU')")
 db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(2,2,'Death','28 MAY 2005','South Coast District Hospital, Victor Harbor, South Australia',NULL,NULL,'DEAT')")
 db.commit()

def test_question_events_are_canonical_timeline_events(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 assert _event_rows(db,1)==timeline_for_person(db,1)["events"]

def test_occupation_uses_canonical_value(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 r=answer_question(db,"What occupation did Kym Knuckey do?",1)
 assert r["status"]=="ok"
 assert r["answer"]=="Kym Wayne Knuckey — Occupations: Intranet Control Administrator [ Santos Ltd. ]."

def test_death_place_uses_canonical_place(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 r=answer_question(db,"Where did Barry Jones die?",1)
 assert r["status"]=="ok"
 assert r["answer"]=="Barry George Jones — Death place: South Coast District Hospital, Victor Harbor, South Australia."

def test_when_death_retained(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 assert "28 MAY 2005" in answer_question(db,"When did Barry Jones die?",1)["answer"]

def test_how_death_remains_conservative(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 r=answer_question(db,"How did Barry Jones die?",1)
 assert r["status"]=="not-found"
 assert r["answer"]=="Barry George Jones died on 28 MAY 2005, but I do not have a recorded cause of death."
