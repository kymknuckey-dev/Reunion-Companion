from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence_matcher import missing_death_candidates, ryerson_death_candidates
from reunion_companion.companion.external_evidence_scan import enqueue_death_research_candidates, queue_rows
from reunion_companion.companion.beta_ui import research_page

def person(db,pid,xref,given,surname,display=None):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
               (pid,xref,pid,given,surname,display or " ".join(x for x in (given,surname) if x),"M",f"{given or ''} /{surname or ''}/"))

def event(db,pid,kind,date=None,place=None,note=None):
    db.execute("INSERT INTO events(person_id,event_type,date_text,place_text,note_text) VALUES(?,?,?,?,?)",(pid,kind,date,place,note))

def family(db,fid,*members):
    db.execute("INSERT INTO families(id,gedcom_xref) VALUES(?,?)",(fid,f"@F{fid}@"))
    for pid,role in members:
        db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,?)",(fid,pid,role))

def test_broad_missing_death_still_includes_surnameless(tmp_path):
    db=connect(tmp_path/"x.db"); person(db,1,"@I1@","Ada",None,"Ada"); db.commit()
    assert [r["display_name"] for r in missing_death_candidates(db)]==["Ada"]

def test_ryerson_requires_surname_only(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Ada",None,"Ada"); person(db,2,"@I2@","John","Knuckey","John Knuckey"); db.commit()
    assert [r["display_name"] for r in ryerson_death_candidates(db)]==["John Knuckey"]

def test_surname_alone_is_eligible(tmp_path):
    db=connect(tmp_path/"x.db"); person(db,1,"@I1@","John","Knuckey","John Knuckey"); db.commit()
    assert len(ryerson_death_candidates(db))==1

def test_stronger_identity_ranks_higher(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","John","Knuckey","John Knuckey")
    person(db,2,"@I2@","Peter Stanly","Rigg","Peter Stanly Rigg")
    person(db,3,"@I3@","Jillian Marie","Cox","Jillian Marie Cox")
    event(db,2,"Birth","21 May 1944","Brighton Community Hospital")
    event(db,2,"Death",None,None,"Death notice information already recorded in note")
    family(db,1,(2,"Husband"),(3,"Wife")); db.commit()
    rows=ryerson_death_candidates(db); names=[r["display_name"] for r in rows]
    assert names.index("Peter Stanly Rigg") < names.index("John Knuckey")

def test_unattended_queue_excludes_surnameless(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Ada",None,"Ada"); person(db,2,"@I2@","John","Knuckey","John Knuckey"); db.commit()
    assert enqueue_death_research_candidates(db)==1
    rows=queue_rows(db); assert len(rows)==1
    assert rows[0]["person_gedcom_xref"]=="@I2@"

def test_research_page_ryerson_section_excludes_surnameless(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Ada",None,"Ada"); person(db,2,"@I2@","Peter Stanly","Rigg","Peter Stanly Rigg")
    event(db,2,"Birth","21 May 1944","Brighton Community Hospital"); db.commit()
    html=research_page(db)
    section=html.split("Ryerson Death Research",1)[1].split("Unsourced Events",1)[0]
    assert "Peter Stanly Rigg" in section
    assert ">Ada<" not in section
