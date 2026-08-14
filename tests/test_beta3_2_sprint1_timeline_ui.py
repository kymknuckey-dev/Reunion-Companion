from pathlib import Path
from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import render_get

def seed(db):
    db.execute("""INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name)
                  VALUES(1,'@I1@',1,'Mervyn','Knuckey','Mervyn Knuckey','M','Mervyn /Knuckey/')""")
    db.execute("INSERT INTO events VALUES(1,1,'Birth','24 SEP 1933','Unley','Y','A birth note','BIRT')")
    db.execute("INSERT INTO events VALUES(2,1,'Occupation','1955','Adelaide','Public Servant','Employment note','OCCU')")
    db.execute("INSERT INTO sources(id,gedcom_xref,title,text,display_text) VALUES(7,'@S7@','Birth Certificate','Birth Certificate.','Birth Certificate.')")
    db.execute("INSERT INTO event_sources VALUES(1,7,'GEDCOM')")
    db.commit()

def test_three_timeline_personas_render(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    story=render_get(db,"/person/1",{"tab":"timeline","view":"story"})
    research=render_get(db,"/person/1",{"tab":"timeline","view":"research"})
    data=render_get(db,"/person/1",{"tab":"timeline","view":"data"})
    # Build 3 collapses the old Story/Research/Data selector by mode.
    for page in (story,research,data):
        assert "Research Timeline" in page
        assert "View event →" in page
        assert "Source 7 — Birth Certificate." in page
        assert "GEDCOM Tag" not in page
    db.close()

def test_event_workspace_renders(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    page=render_get(db,"/event/1",{"view":"research"})
    for heading in ("Overview","Timeline Context","Evidence","Media","Notes","Related People","Review Observations","Raw Event Data"):
        assert heading in page
    assert "Source 7 — Birth Certificate." in page
    db.close()

def test_timeline_navigation_generates_no_reports(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    report_dir=tmp_path/"Documents"/"Reunion Companion Reports"
    render_get(db,"/person/1",{"tab":"timeline","view":"story"})
    render_get(db,"/event/1",{})
    assert not report_dir.exists()
    db.close()
