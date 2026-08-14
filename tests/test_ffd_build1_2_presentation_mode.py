from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import render_get,layout
from reunion_companion.companion.ffd_presentation import (
    presentation_mode_enabled,set_presentation_mode,toggle_presentation_mode
)

def seed(db):
    people=[
      (1,'@I1@',1,'Mervyn Neil','Knuckey','Mervyn Neil Knuckey','M','Mervyn Neil /Knuckey/'),
      (2,'@I2@',2,'Elaine Fay','Cox','Elaine Fay Cox','F','Elaine Fay /Cox/'),
    ]
    db.executemany("""INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name)
                      VALUES(?,?,?,?,?,?,?,?)""",people)
    db.execute("INSERT INTO families(id,gedcom_xref,marriage_date,marriage_place) VALUES(1,'@F1@','1956','Adelaide')")
    db.execute("INSERT INTO family_members VALUES(1,1,'Husband')")
    db.execute("INSERT INTO family_members VALUES(1,2,'Wife')")
    db.execute("INSERT INTO events VALUES(1,1,'Birth','24 SEP 1933','Unley','Y','Birth note','BIRT')")
    db.execute("INSERT INTO sources(id,gedcom_xref,title,text,display_text) VALUES(7,'@S7@','Birth Certificate','Birth Certificate.','Birth Certificate.')")
    db.execute("INSERT INTO event_sources VALUES(1,7,'GEDCOM')")
    db.execute("INSERT INTO imports(source_path,source_type,imported_at) VALUES('/tmp/family.ged','GEDCOM','2026-08-10 07:00:00')")
    db.commit()

def test_mode_defaults_off(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    assert presentation_mode_enabled() is False
    page=layout("Test","<p>Hello</p>")
    assert "<html class=''>" in page
    assert "Presentation Mode" in page

def test_toggle_persists(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    assert toggle_presentation_mode() is True
    assert presentation_mode_enabled() is True
    assert toggle_presentation_mode() is False

def test_home_changes_to_presentation(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    set_presentation_mode(True)
    page=render_get(db,"/",{})
    assert "<html class='presentation'>" in page
    assert "Presentation Mode is ON" in page
    assert "Knuckey Family History" in page
    db.close()

def test_technical_routes_still_exist(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    set_presentation_mode(True)
    for route in ("/quality","/places","/sources","/data"):
        assert "<!doctype html>" in render_get(db,route,{})
    db.close()

def test_person_tabs_are_simpler(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    set_presentation_mode(True)
    page=render_get(db,"/person/1",{})
    assert "Overview" in page and "Timeline" in page and "Biography" in page
    assert "Family" in page and "Media" in page and "Publish" in page
    # Sources is no longer a Presentation navigation tab; source wording may
    # still appear in secondary explanatory/action content.
    from reunion_companion.companion.person_navigation import PRESENTATION_ITEMS
    assert "Sources" not in [label for _,label in PRESENTATION_ITEMS]
    assert "Data Quality" not in page
    set_presentation_mode(False)
    page=render_get(db,"/person/1",{})
    assert "Data Quality" in page and "Confidence" in page and "Research" in page
    db.close()

def test_timeline_intelligence_retained(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    set_presentation_mode(True)
    page=render_get(db,"/person/1",{"tab":"timeline","view":"story"})
    assert "Life Timeline" in page
    assert "Research Timeline" not in page and "Data" not in page
    assert "View event →" not in page
    db.close()

def test_mode_does_not_modify_genealogy(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    before=db.execute("SELECT COUNT(*) FROM people").fetchone()[0]
    set_presentation_mode(True)
    render_get(db,"/",{})
    render_get(db,"/person/1",{})
    set_presentation_mode(False)
    after=db.execute("SELECT COUNT(*) FROM people").fetchone()[0]
    assert before==after
    db.close()

def test_navigation_still_does_not_publish(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    set_presentation_mode(True)
    reports=tmp_path/"Documents"/"Reunion Companion Reports"
    for path,q in [
      ("/",{}),("/search",{}),("/research",{}),("/media",{}),
      ("/person/1",{}),("/person/1",{"tab":"timeline","view":"story"}),("/family/1",{})
    ]:
        render_get(db,path,q)
    assert not reports.exists()
    db.close()
