from pathlib import Path
from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import render_get
from reunion_companion.companion.ffd_shell import (
    load_settings,update_setting,toggle_presentation,publication_library,remember_person,recent_people
)

def seed(db):
    people=[
      (1,'@I1@',1,'Mervyn Neil','Knuckey','Mervyn Neil Knuckey','M','Mervyn Neil /Knuckey/'),
      (2,'@I2@',2,'Elaine Fay','Cox','Elaine Fay Cox','F','Elaine Fay /Cox/'),
      (3,'@I3@',3,'Charles Henry James','Knuckey','Charles Henry James Knuckey','M','Charles Henry James /Knuckey/'),
    ]
    db.executemany("""INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name)
                      VALUES(?,?,?,?,?,?,?,?)""",people)
    db.execute("INSERT INTO families(id,gedcom_xref,marriage_date,marriage_place) VALUES(1,'@F1@','1956','Adelaide')")
    db.execute("INSERT INTO family_members VALUES(1,1,'Husband')")
    db.execute("INSERT INTO family_members VALUES(1,2,'Wife')")
    db.execute("INSERT INTO events VALUES(1,1,'Birth','24 SEP 1933','Unley','Y','Birth note','BIRT')")
    db.execute("INSERT INTO sources(id,gedcom_xref,title,text,display_text) VALUES(7,'@S7@','Birth Certificate','Birth Certificate.','Birth Certificate.')")
    db.execute("INSERT INTO event_sources VALUES(1,7,'GEDCOM')")
    db.execute("INSERT INTO imports(source_path,source_type,imported_at) VALUES('/tmp/family.ged','GEDCOM','2026-08-09 08:00:00')")
    db.commit()

def test_home_is_family_presentation(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    page=render_get(db,"/",{})
    assert "Knuckey Family History" in page
    assert "Research begun by" in page
    assert "Mervyn Neil Knuckey" in page
    assert "Welcome to your family history" in page
    assert "Research preserved for future generations." in page
    assert "First Family Demonstration" in page
    db.close()

def test_new_shell_routes_render(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    for path in ("/search","/people","/families","/books","/settings","/about"):
        page=render_get(db,path,{})
        assert "<!doctype html>" in page,path
        assert "Reunion Companion" in page,path
    db.close()

def test_search_and_recent_people(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    result=render_get(db,"/search",{"q":"Mervyn"})
    assert "Mervyn Neil Knuckey" in result
    render_get(db,"/person/1",{})
    recent=recent_people(db)
    assert recent[0]["display_name"]=="Mervyn Neil Knuckey"
    home=render_get(db,"/",{})
    assert "Recently Viewed" in home and "Mervyn Neil Knuckey" in home
    db.close()

def test_presentation_mode_is_companion_only(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    before=db.execute("SELECT COUNT(*) FROM people").fetchone()[0]
    assert load_settings()["presentation_mode"] is False
    assert toggle_presentation() is True
    page=render_get(db,"/",{})
    assert "<html class='presentation'>" in page
    assert toggle_presentation() is False
    after=db.execute("SELECT COUNT(*) FROM people").fetchone()[0]
    assert before==after
    db.close()

def test_books_library_discovers_but_does_not_generate(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    reports=tmp_path/"Documents"/"Reunion Companion Reports"
    assert not reports.exists()
    page=render_get(db,"/books",{})
    assert "Opening this page never generates a report" in page
    assert not reports.exists()
    reports.mkdir(parents=True)
    f=reports/"Mervyn_Neil_Knuckey_Professional_Family_History.html"
    f.write_text("<html>book</html>")
    items=publication_library()
    assert len(items)==1
    assert items[0]["kind"]=="Family-history Book"
    page=render_get(db,"/books",{})
    assert "Mervyn Neil Knuckey Professional Family History" in page
    db.close()

def test_timeline_intelligence_is_retained(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    page=render_get(db,"/person/1",{"tab":"timeline","view":"story"})
    assert "One event-driven timeline" in page
    assert "Story" in page and "Research" in page and "Data" in page
    db.close()

def test_no_navigation_generates_reports(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    reports=tmp_path/"Documents"/"Reunion Companion Reports"
    for path,q in [
        ("/",{}),("/search",{}),("/people",{}),("/families",{}),
        ("/books",{}),("/about",{}),("/person/1",{}),
        ("/person/1",{"tab":"timeline","view":"story"}),("/family/1",{})
    ]:
        render_get(db,path,q)
    assert not reports.exists()
    db.close()
