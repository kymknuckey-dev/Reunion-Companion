
from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import person_page
from reunion_companion.companion.external_evidence import external_evidence_for_person
from reunion_companion.companion.ryerson_browser_assist import import_copied_ryerson_content

def person(db,pid,xref,given,surname,display=None):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",(pid,xref,pid,given,surname,display or f"{given} {surname}","M",f"{given} /{surname}/"))

def event(db,pid,kind,date=None,place=None,note=None):
    db.execute("INSERT INTO events(person_id,event_type,date_text,place_text,note_text) VALUES(?,?,?,?,?)",(pid,kind,date,place,note))

def test_research_tab_no_longer_shows_manual_ryerson_search_and_import_form(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Peter Stanly","Rigg","Peter Stanly Rigg")
    event(db,1,"Birth","21 May 1944","Brighton Community Hospital")
    event(db,1,"Death",None,None,"Death notice details are in this note")
    db.commit()
    html=person_page(db,1,"research",presentation_override=False)
    assert "External Evidence" in html
    assert "Search Ryerson" not in html
    assert "/research/ryerson/import/1" not in html
    assert "Paste Ryerson result" not in html

def test_recorded_death_does_not_show_ryerson_search_ui(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Complete","Person")
    death=db.execute("INSERT INTO events(person_id,event_type,date_text,place_text) VALUES(1,'Death','01 Jan 2000','Adelaide')").lastrowid
    db.execute("INSERT INTO sources(id,gedcom_xref,title) VALUES(1,'@S1@','Death source')")
    db.execute("INSERT INTO event_sources(event_id,source_id,relation) VALUES(?,1,'GEDCOM')",(death,))
    db.commit()
    html=person_page(db,1,"research",presentation_override=False)
    assert "Paste Ryerson result" not in html

def test_imported_finding_is_visible_on_research_tab(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Peter Stanly","Rigg","Peter Stanly Rigg")
    event(db,1,"Birth","21 May 1944","Brighton Community Hospital")
    db.commit()
    copied=("RIGG\tPeter Stanley\tDeath notice\t02JAN2021\tDeath\t\tlate of Curramulka (born 21 May 1944)\tAdelaide Advertiser\t04JAN2021")
    result=import_copied_ryerson_content(db,1,copied)
    assert result["stored"]==1
    assert len(external_evidence_for_person(db,"@I1@"))==1
    html=person_page(db,1,"research",presentation_override=False)
    assert "Peter Stanley RIGG" in html
    assert "Adelaide Advertiser" in html
    assert "Curramulka" in html
