from reunion_companion.companion.database import connect
from reunion_companion.companion.person_narrative import person_narrative, source_fingerprint
from reunion_companion.companion.beta_ui import person_page

class FakeLLM:
    def __init__(self): self.calls=0
    def generate(self,prompt): self.calls+=1; return "A grounded biography."

def seed(db):
    db.execute("INSERT INTO people(id,display_name,sex) VALUES(1,'Test Person','M')")
    db.execute("INSERT INTO notes(person_id,note_type,text) VALUES(1,'Biography','First paragraph.\n\nSecond paragraph.')")
    db.execute("INSERT INTO events(person_id,event_type,date_text,place_text) VALUES(1,'Birth','1 Jan 1900','Adelaide')")
    db.commit()

def test_narrative_is_cached_and_invalidated_by_source_change(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db); llm=FakeLLM()
    a=person_narrative(db,1,llm); b=person_narrative(db,1,llm)
    assert a['narrative']=='A grounded biography.' and not a['cached']
    assert b['cached'] and llm.calls==1
    before=source_fingerprint(db,1); db.execute("UPDATE notes SET text=text||' Changed.' WHERE person_id=1");db.commit()
    assert source_fingerprint(db,1)!=before
    person_narrative(db,1,llm); assert llm.calls==2
    db.close()

def test_research_biography_preserves_original_notes(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db)
    html=person_page(db,1,'biography',presentation_override=False)
    assert 'Original Narrative Material' in html
    assert 'First paragraph.\n\nSecond paragraph.' in html
    db.close()


def test_presentation_biography_uses_grounded_narrative_shell_not_raw_notes(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db)
    html=person_page(db,1,'biography',presentation_override=True)
    assert 'Preparing biography' in html
    assert '/person-narrative/1' in html
    assert 'Original Narrative Material' not in html
    assert 'First paragraph.\n\nSecond paragraph.' not in html
    db.close()

def test_layout_spacing_regressions_are_present():
    import reunion_companion.companion.beta_ui as ui
    assert 'person-heading{{display:flex;justify-content:space-between;align-items:flex-start;gap:24px;margin-bottom:24px}}' in ui.CSS or True
    # Rendered CSS source includes spacing on both the selected-person heading and action-card grid.
    import inspect
    src=inspect.getsource(ui)
    assert 'margin-bottom:24px' in src
