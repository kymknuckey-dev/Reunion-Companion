from pathlib import Path
import sqlite3
from reunion_companion.companion.publishing_v10 import _media_figure,_person_summary_html

def test_pdf_asset_copy_and_relative_link(tmp_path):
    pdf=tmp_path/"Birth Certificate With Spaces.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")
    out=tmp_path/"Family Chapter.html"
    m={"id":77,"file_path":str(pdf),"title":"Birth Certificate","exists_on_disk":1}
    html=_media_figure(m,output_html=out)
    assets=tmp_path/"Family Chapter_assets"
    copied=list(assets.glob("*.pdf"))
    assert len(copied)==1
    assert "file://" not in html
    assert f"href='{assets.name}/{copied[0].name}'" in html

def test_person_summary_topics_are_stacked(tmp_path):
    db=sqlite3.connect(":memory:")
    db.row_factory=sqlite3.Row
    db.executescript("""
      CREATE TABLE people(id INTEGER PRIMARY KEY,display_name TEXT);
      CREATE TABLE events(id INTEGER PRIMARY KEY,person_id INTEGER,event_type TEXT,date_text TEXT,place_text TEXT,value_text TEXT);
      INSERT INTO people VALUES(1,'Example Person');
      INSERT INTO events VALUES(1,1,'Birth','1 JAN 1900','Adelaide',NULL);
      INSERT INTO events VALUES(2,1,'Death','2 FEB 1980','Adelaide',NULL);
      INSERT INTO events VALUES(3,1,'Occupation',NULL,NULL,'Carpenter');
      INSERT INTO events VALUES(4,1,'Education',NULL,NULL,'Trade School');
      INSERT INTO events VALUES(5,1,'Religion',NULL,NULL,'Church of England');
    """)
    html=_person_summary_html(db,1)
    assert "<h3>Born</h3><p>1 JAN 1900 — Adelaide</p>" in html
    assert "<h3>Died</h3><p>2 FEB 1980 — Adelaide</p>" in html
    assert "<h3>Occupation</h3><p>Carpenter</p>" in html
    assert "<h3>Education</h3><p>Trade School</p>" in html
    assert "<h3>Religion</h3><p>Church of England</p>" in html
    assert "<dl>" not in html
