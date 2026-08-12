from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import render_get
from reunion_companion.companion.ffd_presentation import set_presentation_mode
def seed(db):
 db.executemany("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",[(1,'@I1@',1,'Mervyn Neil','Knuckey','Mervyn Neil Knuckey','M','Mervyn Neil /Knuckey/'),(2,'@I2@',2,'Elaine Fay','Cox','Elaine Fay Cox','F','Elaine Fay /Cox/')]);db.execute("INSERT INTO families(id,gedcom_xref,marriage_date,marriage_place) VALUES(1,'@F1@','1956','Adelaide')");db.execute("INSERT INTO family_members VALUES(1,1,'Husband')");db.execute("INSERT INTO family_members VALUES(1,2,'Wife')");db.execute("INSERT INTO events VALUES(1,1,'Birth','24 SEP 1933','Unley','Y','Birth note','BIRT')");db.execute("INSERT INTO events VALUES(2,1,'Residence','1955','Adelaide','Y','Living in Adelaide','RESI')");db.commit()
def test_story(tmp_path,monkeypatch):
 monkeypatch.setenv("HOME",str(tmp_path));db=connect(tmp_path/"x.sqlite3");seed(db);set_presentation_mode(True);p=render_get(db,"/person/1",{});assert all(x in p for x in ("A life in the family history","Born 1933","Elaine Fay Cox","/event/1","Birth note","Overview","Timeline","Biography"))
def test_normal(tmp_path,monkeypatch):
 monkeypatch.setenv("HOME",str(tmp_path));db=connect(tmp_path/"x.sqlite3");seed(db);set_presentation_mode(False);assert "A life in the family history" not in render_get(db,"/person/1",{})
def test_deep_links(tmp_path,monkeypatch):
 monkeypatch.setenv("HOME",str(tmp_path));db=connect(tmp_path/"x.sqlite3");seed(db);set_presentation_mode(True);p=render_get(db,"/person/1",{});assert all(x in p for x in ("tab=timeline","tab=biography","tab=family","tab=media","tab=sources","tab=publish"))
def test_timeline(tmp_path,monkeypatch):
 monkeypatch.setenv("HOME",str(tmp_path));db=connect(tmp_path/"x.sqlite3");seed(db);set_presentation_mode(True);p=render_get(db,"/person/1",{"tab":"timeline","view":"story"});assert all(x in p for x in ("One event-driven timeline","Story","Research","Data"))
def test_event(tmp_path,monkeypatch):
 monkeypatch.setenv("HOME",str(tmp_path));db=connect(tmp_path/"x.sqlite3");seed(db);set_presentation_mode(True);assert "<!doctype html>" in render_get(db,"/event/1",{})
def test_read_only(tmp_path,monkeypatch):
 monkeypatch.setenv("HOME",str(tmp_path));db=connect(tmp_path/"x.sqlite3");seed(db);n=db.execute("SELECT COUNT(*) FROM people").fetchone()[0];set_presentation_mode(True);render_get(db,"/person/1",{});assert db.execute("SELECT COUNT(*) FROM people").fetchone()[0]==n
