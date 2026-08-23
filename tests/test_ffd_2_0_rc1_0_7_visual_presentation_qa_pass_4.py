from pathlib import Path
from reunion_companion.companion.ffd_person_story import _event_sort_key

ROOT=Path(__file__).resolve().parents[1]

class E(dict):
    def __getitem__(self, key): return dict.get(self,key)

def event(i,kind,date=''):
    return E(id=i,event_type=kind,date_text=date,gedcom_tag='')

def test_visual_pass4_release_identity():
    assert 'APP_RELEASE="FFD 2.0 RC1.0.10 — Multi-page PDF Reproduction"' in (ROOT/'macos_app/build_app.py').read_text()

def test_visual_pass4_is_one_continuous_life_story_without_recorded_facts_section():
    s=(ROOT/'src/reunion_companion/companion/ffd_person_story.py').read_text()
    assert "ffd-life-timeline" in s
    assert "ffd-recorded-facts" not in s
    assert "Recorded facts" not in s

def test_visual_pass4_keeps_undated_facts_but_death_and_disposition_terminal():
    events=[event(1,'Birth','1935'),event(2,'Education'),event(3,'Religion'),event(4,'Death','2005'),event(5,'Burial')]
    ordered=sorted(events,key=_event_sort_key)
    assert [e['event_type'] for e in ordered]==['Birth','Education','Religion','Death','Burial']

def test_visual_pass4_burial_is_last_even_if_undated_or_oddly_numbered():
    events=[event(9,'Burial'),event(2,'Occupation'),event(8,'Death','2005'),event(1,'Birth','1935')]
    ordered=sorted(events,key=_event_sort_key)
    assert ordered[-1]['event_type']=='Burial'
    assert ordered[-2]['event_type']=='Death'

def test_visual_pass4_continuous_spine_and_dots_apply_to_dated_and_undated_rows():
    s=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    assert '.ffd-life-timeline .ffd-chronology:before' in s
    assert '.ffd-chronology-dot' in s
    assert '.ffd-milestone-undated .ffd-milestone-date' in s
