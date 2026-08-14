from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import person_page
from reunion_companion.companion.person_navigation import PRESENTATION_ITEMS, RESEARCH_ITEMS
from reunion_companion.companion.version_identity import FFD_BUILD, RELEASE_TAG

def seed(db):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(1,'@I1@',1,'Mervyn Neil','Knuckey','Mervyn Neil Knuckey','M','Mervyn Neil /Knuckey/')")
    db.execute("INSERT INTO events VALUES(1,1,'Marriage','1 JAN 1960','Adelaide',NULL,'Marriage event note','MARR')")
    db.execute("INSERT INTO notes(id,person_id,note_type,gedcom_tag,text) VALUES(1,1,'Misc','NOTE','Research notes text')")
    db.execute("INSERT INTO sources(id,gedcom_xref,title,text,display_text) VALUES(2,'@S2@','Marriage Certificate',NULL,'Marriage Certificate')")
    db.execute("INSERT INTO sources(id,gedcom_xref,title,text,display_text) VALUES(5,'@S5@','Research by Mervyn Neil Knuckey',NULL,'Research by Mervyn Neil Knuckey')")
    db.execute("INSERT INTO event_sources VALUES(1,2,'GEDCOM')")
    db.execute("INSERT INTO note_sources VALUES(1,5,'GEDCOM')")
    db.commit()

def test_presentation_timeline(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db); html=person_page(db,1,'timeline',presentation_override=True)
    assert 'Life Timeline' in html and 'Research Timeline' not in html and 'View event →' not in html
    assert 'Source [1]' in html and 'Marriage Certificate' in html

def test_research_timeline(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db); html=person_page(db,1,'timeline',presentation_override=False)
    assert 'Research Timeline' in html and 'View event →' in html and 'Marriage Certificate' in html

def test_navigation():
    assert 'Sources' not in [x[1] for x in PRESENTATION_ITEMS]
    assert 'Sources' in [x[1] for x in RESEARCH_ITEMS]

def test_source_context(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db); html=person_page(db,1,'sources',presentation_override=False)
    assert 'Marriage Certificate' in html and 'Attached to:' in html and 'Marriage' in html
    assert 'Research by Mervyn Neil Knuckey' in html and ('Misc' in html or 'Misc Notes' in html)

def test_identity():
    # Historical Build 3 regression: current releases may advance identity.
    assert FFD_BUILD
    assert RELEASE_TAG == f"ffd-1.9-build-{FFD_BUILD}"
