from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import render_get
from reunion_companion.companion.ffd_presentation import set_presentation_mode
def seed(db):
 db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(1,'@I1@',1,'Mervyn','Knuckey','Mervyn Knuckey','M','Mervyn /Knuckey/')")
 db.execute("INSERT INTO events VALUES(1,1,'Birth','24 SEP 1933','Unley','Y','Birth note','BIRT')");db.commit()
def test_timeline_views(tmp_path,monkeypatch):
 monkeypatch.setenv("HOME",str(tmp_path));db=connect(tmp_path/"x.sqlite3");seed(db);set_presentation_mode(True)
 for view in ("story","research","data"):
  p=render_get(db,"/person/1",{"tab":"timeline","view":view})
  assert "Life Timeline" in p and "View event →" not in p
 db.close()
def test_event_return(tmp_path,monkeypatch):
 monkeypatch.setenv("HOME",str(tmp_path));db=connect(tmp_path/"x.sqlite3");seed(db);set_presentation_mode(True)
 for view in ("story","research","data"):
  p=render_get(db,"/event/1",{"view":view})
  assert "ffd-back-link" in p and "← Timeline" in p
  assert f"/person/1?tab=timeline&view={view}" in p
 db.close()
def test_workspace_content_retained(tmp_path,monkeypatch):
 monkeypatch.setenv("HOME",str(tmp_path));db=connect(tmp_path/"x.sqlite3");seed(db);set_presentation_mode(True)
 p=render_get(db,"/event/1",{"view":"story"})
 assert all(x in p for x in ("Overview","Timeline Context","Evidence","Media","Notes","Raw Event Data"))
 db.close()
