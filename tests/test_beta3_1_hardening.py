from pathlib import Path
import os
from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import render_get

def seed(db):
    db.execute("""INSERT INTO people
      (id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name)
      VALUES(1,'@I1@',1,'Charles Henry James','Knuckey','Charles Henry James Knuckey','M','Charles Henry James /Knuckey/')""")
    db.execute("""INSERT INTO people
      (id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name)
      VALUES(2,'@I2@',2,'Elizabeth Anne','Hunter','Elizabeth Anne Hunter','F','Elizabeth Anne /Hunter/')""")
    db.execute("INSERT INTO families(id,gedcom_xref,marriage_date,marriage_place) VALUES(1,'@F1@','1900','Adelaide S.A.')")
    db.execute("INSERT INTO family_members VALUES(1,1,'Husband')")
    db.execute("INSERT INTO family_members VALUES(1,2,'Wife')")
    db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(1,1,'Birth','1875','Adelaide S.A.',NULL,NULL,'BIRT')")
    db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(2,1,'Occupation','1895',NULL,'Carpenter','Apprenticed locally.','OCCU')")
    db.execute("INSERT INTO notes(id,person_id,note_type,gedcom_tag,text,is_referenced) VALUES(1,1,'Research','HIST','Family research note.',0)")
    db.execute("INSERT INTO sources(id,gedcom_xref,title,text,display_text) VALUES(1,'@S1@','Birth Certificate','Birth Certificate.','Birth Certificate.')")
    db.execute("INSERT INTO event_sources VALUES(1,1,'GEDCOM')")
    db.execute("INSERT INTO media(id,gedcom_xref,file_path,title,exists_on_disk) VALUES(1,NULL,'/tmp/missing.jpg','Portrait',0)")
    db.execute("INSERT INTO person_media VALUES(1,1,'GEDCOM')")
    db.execute("INSERT INTO imports(source_path,source_type,imported_at) VALUES('/tmp/example.ged','GEDCOM','2026-08-09 08:00:00')")
    db.commit()

def test_all_top_level_pages_render(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"companion.sqlite3");seed(db)
    pages=[
      ("/",{}),("/data",{}),("/quality",{}),("/research",{}),("/places",{}),
      ("/sources",{}),("/media",{}),("/media",{"category":"Missing"}),
      ("/media-item/1",{}),("/publishing",{}),("/family/1",{})
    ]
    for path,q in pages:
        html=render_get(db,path,q)
        assert "<!doctype html>" in html, path
        assert "Beta 3." in html, path
        assert "Page Error" not in html, path
    db.close()

def test_all_person_tabs_render(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"companion.sqlite3");seed(db)
    tabs=["overview","timeline","biography","family","sources","media","confidence","research","data-quality","publish"]
    for tab in tabs:
        html=render_get(db,"/person/1",{"tab":tab})
        assert "Charles Henry James Knuckey" in html, tab
        assert "Page Error" not in html, tab
    db.close()

def test_get_pages_do_not_generate_reports(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"companion.sqlite3");seed(db)
    report_dir=tmp_path/"Documents"/"Reunion Companion Reports"
    assert not report_dir.exists()
    for path,q in [
      ("/",{}),("/data",{}),("/quality",{}),("/publishing",{}),
      ("/person/1",{"tab":"publish"}),("/family/1",{})
    ]:
        render_get(db,path,q)
    assert not report_dir.exists()
    db.close()

def test_data_quality_and_publishing_are_defined(tmp_path):
    db=connect(tmp_path/"companion.sqlite3");seed(db)
    assert "Data Manager" in render_get(db,"/data",{})
    assert "Data Quality Centre" in render_get(db,"/quality",{})
    assert "Reports" in render_get(db,"/publishing",{})
    db.close()
