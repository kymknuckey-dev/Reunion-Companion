import base64
from reunion_companion.companion.database import connect
from reunion_companion.companion.queries import search_people as query_search_people
from reunion_companion.companion.beta_ui_service import search_people as ui_search_people
from reunion_companion.companion.person_narrative import person_narrative
from reunion_companion.companion.publishing_v11 import _person_section, _media_block, media_source_labels
from reunion_companion.companion.descendant_chart import chart_html

PNG=base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl2n0kAAAAASUVORK5CYII=")

def seed(db,tmp_path):
    photo=tmp_path/"Kym Wayne.jpg"; photo.write_bytes(PNG)
    cert=tmp_path/"Marriage Certificate.jpg"; cert.write_bytes(PNG)
    db.executescript("""
    INSERT INTO people(id,given_names,surname,display_name,sex) VALUES
      (1,'Kym Wayne','Knuckey','Kym Wayne Knuckey','M'),
      (2,'Sue Anne','Example','Sue Anne Example','F'),
      (3,'Mitchell','Knuckey','Mitchell Knuckey','M');
    INSERT INTO families(id,marriage_date,marriage_place) VALUES(1,'1 JAN 1980','Adelaide');
    INSERT INTO family_members(family_id,person_id,role) VALUES
      (1,1,'Husband'),(1,2,'Wife'),(1,3,'Child');
    INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text) VALUES
      (1,1,'Birth','1 JAN 1955','Adelaide',NULL),
      (2,1,'Christening','1 FEB 1955','Adelaide',NULL),
      (3,1,'Religion',NULL,NULL,'Uniting Church'),
      (4,1,'Education',NULL,NULL,'Brighton High School'),
      (5,1,'Occupation',NULL,NULL,'Engineer'),
      (6,2,'Birth','2 FEB 1956','Adelaide',NULL);
    INSERT INTO notes(id,person_id,note_type,gedcom_tag,text) VALUES
      (1,1,'Biography','NOTE','Kym played sport and worked in Adelaide.');
    INSERT INTO sources(id,gedcom_xref,title,display_text) VALUES
      (12,'@S12@','Marriage Certificate','South Australian Marriage Certificate');
    INSERT INTO event_sources(event_id,source_id,relation) VALUES(1,12,'GEDCOM');
    """)
    cur=db.execute("INSERT INTO media(gedcom_xref,file_path,title,media_type,exists_on_disk,attachment_scope,attachment_label) VALUES(NULL,?,'Kym portrait','image/jpeg',1,'person','Portrait')",(str(photo),))
    portrait=cur.lastrowid
    db.execute("INSERT INTO person_media(person_id,media_id,relation) VALUES(1,?,'GEDCOM')",(portrait,))
    cur=db.execute("INSERT INTO media(gedcom_xref,file_path,title,media_type,exists_on_disk,attachment_scope,attachment_label) VALUES(NULL,?,'Marriage Certificate','image/jpeg',1,'person','Marriage Certificate')",(str(cert),))
    cert_id=cur.lastrowid
    db.execute("INSERT INTO family_media(family_id,media_id,relation) VALUES(1,?,'GEDCOM')",(cert_id,))
    db.execute("INSERT INTO family_sources(family_id,source_id,relation) VALUES(1,12,'GEDCOM')")
    db.commit()
    return portrait,cert_id

def test_component_search_matches_first_and_surname_across_middle_name(tmp_path):
    db=connect(tmp_path/"x.sqlite3");seed(db,tmp_path)
    assert [r["display_name"] for r in query_search_people(db,"Kym Knuckey")] == ["Kym Wayne Knuckey"]
    assert [r["display_name"] for r in ui_search_people(db,"Kym Knuckey")] == ["Kym Wayne Knuckey"]

def test_canonical_biography_reused_until_explicit_regeneration(tmp_path):
    db=connect(tmp_path/"x.sqlite3");seed(db,tmp_path)
    class Fake:
        def __init__(self):self.calls=0
        def generate(self,prompt):
            self.calls+=1
            assert "given/first name naturally" in prompt
            assert "Do not refer to the subject as Mr, Mrs, Ms, Miss" in prompt
            return "Kym Wayne Knuckey was born in Adelaide.\n\nKym worked in Adelaide."
    llm=Fake()
    a=person_narrative(db,1,llm); assert llm.calls==1
    db.execute("UPDATE notes SET text=text||' Updated.' WHERE id=1");db.commit()
    b=person_narrative(db,1,llm); assert b["narrative"]==a["narrative"] and llm.calls==1
    person_narrative(db,1,llm,force=True); assert llm.calls==2

def test_publication_reuses_same_stored_biography_and_removes_duplicate_summary(tmp_path):
    db=connect(tmp_path/"x.sqlite3");seed(db,tmp_path)
    class Fake:
        def generate(self,prompt):return "Kym Wayne Knuckey was born in Adelaide.\n\nKym enjoyed sport."
    person_narrative(db,1,Fake())
    html=_person_section(db,1,None)
    assert "<h3>Biography</h3>" in html and "Kym enjoyed sport." in html
    assert "Life &amp; Biography" in html and "Life &amp; Notes" not in html
    assert html.index("<h2>Kym Wayne Knuckey</h2>") < html.index("<h3>Biography</h3>")

def test_life_notes_are_deterministic_topic_lines(tmp_path):
    db=connect(tmp_path/"x.sqlite3");seed(db,tmp_path)
    html=_person_section(db,1,None)
    assert "Birth Date" in html and "Birth Place" in html
    assert html.index("Occupation") < html.index("Education") < html.index("Religion")
    assert "Father" not in html  # seed has no parents
    assert "Spouse" in html and "Marriage Date" in html and "Marriage Place" in html
    assert "Children" in html

def test_media_and_fact_sources_use_numbered_reader_facing_citations(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_,cert=seed(db,tmp_path)
    assert media_source_labels(db,cert)==["[12]"]
    row=db.execute("SELECT * FROM media WHERE id=?",(cert,)).fetchone()
    media_html=_media_block(row,None,family_names="Kym Wayne Knuckey and Sue Anne Example",db=db)
    assert "Marriage Certificate" in media_html and "[12]" in media_html
    html=_person_section(db,1,None)
    assert "<h3>Sources</h3>" in html and "[12]" in html

def test_family_and_descendants_attaches_dates_to_each_spouse(tmp_path):
    db=connect(tmp_path/"x.sqlite3");seed(db,tmp_path)
    html=chart_html(db,1,2,3)
    assert "Family &amp; Descendants" in html
    assert "<strong>Husband:</strong>" in html and "Kym Wayne Knuckey" in html and "b. 1 JAN 1955" in html
    assert "<strong>Wife:</strong>" in html and "Sue Anne Example" in html and "b. 2 FEB 1956" in html

def test_other_photo_layout_is_publication_page_driven():
    from reunion_companion.companion import publishing_v11 as pub
    assert ".photo-grid { display:block; }" in pub.PRO_CSS
    assert ".photo-page.photo-pair" in pub.PRO_CSS

def test_rc1_identity_preserves_engine_and_backend_protocol():
    from reunion_companion import app_identity
    assert app_identity.APP_RELEASE_DISPLAY.startswith("FFD 2.0 RC1")
    assert app_identity.APP_RELEASE_NAME in ("Release Candidate Stabilisation","Image Pagination Repair","Birth Document Section Pagination","Birth Document Fitted Page Structural Repair")
    assert app_identity.ENGINE_BASELINE=="FFD 1.9 RC1"
