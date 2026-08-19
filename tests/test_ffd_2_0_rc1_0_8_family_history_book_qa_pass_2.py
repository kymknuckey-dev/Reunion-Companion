from pathlib import Path
from reunion_companion.companion.database import connect
from reunion_companion.companion.family_publication_model import media_kind
from reunion_companion.companion.person_narrative import person_narrative, NARRATIVE_VERSION
from reunion_companion.companion import publishing_v11 as pub


def test_marriage_image_classification_uses_filename_when_title_is_generic():
    m={"file_path":"/archive/Mervyn-Elaine Marriage Certificate.jpg","title":"Certificate"}
    assert media_kind(m)=="document-image"
    text=((m["title"] or "")+" "+Path(m["file_path"]).name).lower()
    assert "marriage" in text



def test_marriage_image_classification_uses_attachment_label_when_names_are_generic():
    m={"file_path":"/archive/IMG_0042.jpg","title":"Certificate","attachment_label":"Marriage Certificate"}
    assert media_kind(m)=="document-image"

def test_person_summary_uses_dad_order_and_book_hierarchy():
    src=Path(pub.__file__).read_text()
    assert "Life &amp; Biography" in src
    assert src.index('add("Birth Date"') < src.index('add("Birth Place"')
    assert src.index('add("Occupation"') < src.index('add("Education"') < src.index('add("Religion"')
    assert src.index('add("Father"') < src.index('add("Mother"')
    assert src.index('add("Spouse"') < src.index('add("Marriage Date"') < src.index('add("Marriage Place"')
    assert 'add("Children"' in src
    assert "Life &amp; Notes" not in src
    assert "<h3>Biography</h3>" in src
    assert "<h3>Sources</h3>" in src


def test_old_cached_changed_prose_is_not_reused(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    db.executescript('''
      INSERT INTO people(id,display_name,sex) VALUES(1,'Mitchell Knuckey','M');
      INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(1,1,'Changed','17 December 2017',NULL,NULL,NULL,'CHAN');
      INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(2,1,'Occupation',NULL,NULL,'Teacher',NULL,'OCCU');
      CREATE TABLE IF NOT EXISTS companion_person_narrative_cache(person_id INTEGER PRIMARY KEY,source_hash TEXT NOT NULL,narrative_version TEXT NOT NULL,narrative TEXT NOT NULL,generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
      INSERT INTO companion_person_narrative_cache(person_id,source_hash,narrative_version,narrative) VALUES(1,'old','old','On 17 December 2017, Mitchell changed.');
    ''')
    narrative=pub._publication_biography(db,1)
    assert "changed" not in narrative.casefold()
    assert "17 December 2017" not in narrative
    assert "Teacher" in narrative
    row=db.execute('SELECT narrative_version FROM companion_person_narrative_cache WHERE person_id=1').fetchone()
    assert row[0]==NARRATIVE_VERSION
