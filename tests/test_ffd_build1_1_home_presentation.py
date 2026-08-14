from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import render_get,layout

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

def test_ffd_home_renders(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    page=render_get(db,"/",{})
    assert "Welcome to your family history" in page
    assert "Knuckey Family History" in page
    assert "Research begun by" in page
    assert "Mervyn Neil Knuckey" in page
    assert "Family History at a Glance" in page
    assert "FFD 1.1" in page
    db.close()

def test_search_route_and_old_query_route_both_work(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    assert "Mervyn Neil Knuckey" in render_get(db,"/search",{"q":"Mervyn"})
    assert "Mervyn Neil Knuckey" in render_get(db,"/",{"q":"Mervyn"})
    db.close()

def test_timeline_intelligence_unchanged(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    page=render_get(db,"/person/1",{"tab":"timeline","view":"story"})
    assert "Research Timeline" in page
    assert "View event →" in page
    assert "/event/1?view=research" in page
    db.close()

def test_existing_top_level_routes_remain(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    for path in ("/data","/quality","/research","/places","/sources","/media","/publishing"):
        page=render_get(db,path,{})
        assert "<!doctype html>" in page,path
        assert "Reunion Companion" in page,path
    db.close()

def test_navigation_does_not_publish(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    reports=tmp_path/"Documents"/"Reunion Companion Reports"
    for path,q in [
      ("/",{}),("/search",{}),("/research",{}),("/quality",{}),
      ("/person/1",{}),("/person/1",{"tab":"timeline","view":"story"}),("/family/1",{})
    ]:
        render_get(db,path,q)
    assert not reports.exists()
    db.close()

def test_historical_branding_tests_remain_compatible():
    page=layout("Test","<p>Hello</p>")
    assert "Beta 3.1" in page
    assert "Beta 3.2" in page
    assert "Research" in page and "Publishing" in page
