from reunion_companion.companion.database import connect
from reunion_companion.companion.publishing_v11 import _family_intro
from reunion_companion.companion.story_engine import story_sections
from reunion_companion.companion.descendant_chart import chart_html
from reunion_companion.companion.publication_narrative import publication_narrative
from reunion_companion.companion.version_identity import FFD_DISPLAY, RELEASE_TAG


def seed(db):
    db.executescript('''
    INSERT INTO people(id,display_name,sex) VALUES(1,'Henry Example','M'),(2,'Alice Example','F'),(3,'Child Example','M'),(4,'Partner Example','F');
    INSERT INTO families(id,marriage_date,marriage_place) VALUES(1,'1 Jan 1950','Adelaide'),(2,NULL,NULL);
    INSERT INTO family_members(family_id,person_id,role) VALUES(1,1,'Husband'),(1,2,'Wife'),(1,3,'Child'),(2,3,'Husband'),(2,4,'Wife');
    INSERT INTO events(person_id,event_type,value_text) VALUES(1,'Occupation','Carpenter'),(1,'Education','Technical School');
    INSERT INTO notes(person_id,note_type,gedcom_tag,text) VALUES(1,'Biography','NOTE','First paragraph.\r\n\r\nSecond paragraph.');
    '''); db.commit()


def test_family_intro_is_reader_facing_and_not_redundant(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db);html=_family_intro(db,1)
    assert "<span class='couple-name'>Henry Example</span><span class='couple-and'>and</span><span class='couple-name'>Alice Example</span>" in html
    assert 'overview-grid' not in html and 'Marriage place' not in html
    assert 'They had 1 child.' in html
    assert 'imported Reunion family records' not in html


def test_research_story_preserves_note_layout_and_work_facts_break_lines(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db); sections=story_sections(db,1); d=dict(sections)
    assert d['Biography']=='First paragraph.\n\nSecond paragraph.'
    assert 'Occupation: Carpenter.\nEducation: Technical School.' in d['Education & Working Life']


def test_descendant_chart_includes_spouses(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db);html=chart_html(db,1,2,4)
    assert 'Henry Example &amp; Alice Example' in html
    assert 'Child Example &amp; Partner Example' in html


def test_publication_narrative_is_grounded_prompt_and_preserves_fallback():
    class Fake:
        def generate(self,prompt):
            assert 'Use ONLY facts' in prompt
            assert 'Original line one.\n\nOriginal line two.' in prompt
            return 'Polished but grounded.'
    assert publication_narrative('Henry',['Original line one.\r\n\r\nOriginal line two.'],['Occupation — Carpenter'],Fake())=='Polished but grounded.'


def test_release_identity_is_ffd_1_9_series():
    assert FFD_DISPLAY.startswith('FFD 1.9 Build ')
    assert RELEASE_TAG.startswith('ffd-1.9-build-')
