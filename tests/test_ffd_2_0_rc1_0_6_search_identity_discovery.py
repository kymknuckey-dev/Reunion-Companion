from reunion_companion.companion.database import connect
from reunion_companion.companion.identity_discovery import resolve_identity_name
from reunion_companion.companion.beta_ui_service import search_people
from reunion_companion.companion.ffd_relationship_questions import answer_question
from reunion_companion.companion.beta_ui import render_get


def seed(db):
    db.executescript("""
    INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES
      (1,'@I1@',1,'Kym Wayne','Knuckey','Kym Wayne Knuckey','M','Kym Wayne /Knuckey/'),
      (2,'@I2@',2,'Susan Lee','Jones','Susan Lee Jones','F','Susan Lee /Jones/'),
      (3,'@I3@',3,'Susan Mary','Knuckey','Susan Mary Knuckey','F','Susan Mary /Knuckey/');
    INSERT INTO families(id,gedcom_xref,marriage_date,marriage_place) VALUES(1,'@F1@','2 JUL 1988','Blackwood');
    INSERT INTO family_members(family_id,person_id,role) VALUES(1,1,'Husband'),(1,2,'Wife');
    INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES
      (10,2,'Residence','1990','Aberfoyle Park, South Australia',NULL,NULL,'RESI'),
      (11,3,'Birth','1 JAN 1970','Adelaide, South Australia',NULL,NULL,'BIRT');
    """)
    db.commit()


def test_marriage_associated_surname_finds_recorded_maiden_identity(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    matches=resolve_identity_name(db,'Susan Knuckey')
    by_name={p['display_name']:p for p in matches}
    assert 'Susan Lee Jones' in by_name
    assert by_name['Susan Lee Jones']['_identity_match_kind']=='spouse-surname'
    assert 'Kym Wayne Knuckey' in by_name['Susan Lee Jones']['_identity_match_reason']
    assert by_name['Susan Lee Jones']['display_name']=='Susan Lee Jones'


def test_given_variant_plus_marriage_association_finds_sue_knuckey(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    matches=resolve_identity_name(db,'Sue Knuckey')
    susan=next(p for p in matches if p['display_name']=='Susan Lee Jones')
    assert susan['_identity_match_kind']=='given-variant-spouse-surname'
    assert 'variation of Susan' in susan['_identity_match_reason']
    assert 'marriage/partnership' in susan['_identity_match_reason']


def test_direct_name_search_adds_association_without_rewriting_reunion_identity(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    names=[p['display_name'] for p in search_people(db,'Sue Knuckey')]
    assert 'Susan Lee Jones' in names
    assert 'Sue Knuckey' not in names


def test_question_before_person_selection_resolves_associated_name_and_answers(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    r=answer_question(db,'Where did Sue Knuckey live?')
    # A real Susan Knuckey also exists, so the question remains explicitly ambiguous.
    assert r['status']=='ambiguous'
    assert r['kind']=='identity-choice'
    ids={c['person']['id'] for c in r['choices']}
    assert ids=={2,3}
    by_id={c['person']['id']:c for c in r['choices']}
    assert by_id[2]['question_relevant'] is True
    assert 'marriage/partnership' in by_id[2]['identity_reason']


def test_selected_discovery_candidate_answers_on_search_page_and_links_to_recorded_person(tmp_path,monkeypatch):
    monkeypatch.setenv('HOME',str(tmp_path))
    db=connect(tmp_path/'x.sqlite3');seed(db)
    html=render_get(db,'/search',{'q':'Where did Sue Knuckey live?','selected':'2'})
    assert 'Aberfoyle Park, South Australia' in html
    assert 'View Susan Lee Jones' in html
    assert '/person/2' in html
    assert "Reunion's recorded name has not been changed" in html


def test_search_page_invites_names_or_questions(tmp_path,monkeypatch):
    monkeypatch.setenv('HOME',str(tmp_path))
    db=connect(tmp_path/'x.sqlite3');seed(db)
    html=render_get(db,'/search',{})
    assert 'Search the Family' in html
    assert 'Find a person, or ask a question about someone in your family history.' in html
    assert 'Where did Susan Knuckey live?' in html


def test_exact_recorded_name_stays_stronger_than_association(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    matches=resolve_identity_name(db,'Susan Knuckey')
    assert matches[0]['display_name']=='Susan Mary Knuckey'
    assert matches[0]['_identity_match_kind']=='recorded-name'


def seed_many_susan_knuckeys(db):
    seed(db)
    # More than a normal top-N ambiguity screen can comfortably display.
    for i in range(4,16):
        year=1800+i
        db.execute(
            "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
            (i,f'@I{i}@',i,'Susan','Knuckey','Susan Knuckey','F','Susan /Knuckey/')
        )
        db.execute(
            "INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(?,?,?,?,?,?,?,?)",
            (100+i,i,'Birth',f'1 JAN {year}','Cornwall, England',None,None,'BIRT')
        )
    db.commit()


def test_many_exact_names_do_not_hide_marriage_associated_candidate(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed_many_susan_knuckeys(db)
    r=answer_question(db,'Where did Susan Knuckey live?')
    assert r['status']=='ambiguous'
    ids={c['person']['id'] for c in r['choices']}
    assert 2 in ids  # Susan Lee Jones remains discoverable through Kym Wayne Knuckey.
    susan=next(c for c in r['choices'] if c['person']['id']==2)
    assert susan['identity_match_kind']=='spouse-surname'
    assert 'Kym Wayne Knuckey' in susan['identity_reason']
    assert susan['question_relevant'] is True


def test_identity_strength_precedes_question_relevance_across_match_groups(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    # Susan Lee Jones has Residence information, while the direct Susan Mary Knuckey does not.
    r=answer_question(db,'Where did Susan Knuckey live?')
    assert r['status']=='ambiguous'
    from reunion_companion.companion.ffd_relationship_questions import _identity_choice_sort_key
    ordered=sorted(r['choices'],key=_identity_choice_sort_key)
    assert ordered[0]['person']['display_name']=='Susan Mary Knuckey'
    assert ordered[0]['identity_group_rank'] < next(c for c in ordered if c['person']['id']==2)['identity_group_rank']


def test_ambiguity_choices_include_recognition_context(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    r=answer_question(db,'Who did Susan Knuckey marry?')
    assoc=next(c for c in r['choices'] if c['person']['id']==2)
    assert 'Spouse: Kym Wayne Knuckey' in assoc['recognition']


def test_search_question_groups_direct_and_associated_people_and_keeps_association_visible(tmp_path,monkeypatch):
    monkeypatch.setenv('HOME',str(tmp_path))
    db=connect(tmp_path/'x.sqlite3');seed_many_susan_knuckeys(db)
    html=render_get(db,'/search',{'q':'Where did Susan Knuckey live?'})
    assert 'Best likely matches' in html
    assert 'People recorded with this name' in html
    assert 'Susan Lee Jones' in html
    assert 'Kym Wayne Knuckey' in html
    # Direct matches are collapsed after the first six rather than crowding out associations.
    assert 'More people recorded with this name' in html


def test_plain_name_search_groups_family_associations_separately(tmp_path,monkeypatch):
    monkeypatch.setenv('HOME',str(tmp_path))
    db=connect(tmp_path/'x.sqlite3');seed(db)
    html=render_get(db,'/search',{'q':'Susan Knuckey'})
    assert 'Best likely matches' in html
    assert 'People recorded with this name' in html
    assert 'Susan Mary Knuckey' in html
    assert 'Susan Lee Jones' in html


def test_literal_display_name_beats_component_given_name_variant(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    # Simulate a Reunion display name of Sue while the formal component remains Susan.
    db.execute("UPDATE people SET display_name='Sue Knuckey', given_names='Susan' WHERE id=3")
    db.commit()
    matches=resolve_identity_name(db,'Sue Knuckey')
    assert matches[0]['id']==3
    assert matches[0]['_identity_match_kind']=='recorded-name'
    assert matches[0]['_identity_match_reason']=='Exact recorded name'


def test_susan_query_keeps_literal_susan_ahead_of_sue_variant(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(4,'@I4@',4,'Susan','Knuckey','Sue Knuckey','F','Susan /Knuckey/')")
    db.commit()
    matches=resolve_identity_name(db,'Susan Knuckey')
    assert matches[0]['display_name']=='Susan Mary Knuckey'
    sue=next(p for p in matches if p['display_name']=='Sue Knuckey')
    assert sue['_identity_match_kind']=='given-variant'


def test_combined_variant_marriage_association_is_prominent_among_associations(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    # Add a weak placeholder-style exact-Sue association to another Knuckey.
    db.executescript("""
      INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES
        (4,'@I4@',4,'Robert','Knuckey','Robert Knuckey','M','Robert /Knuckey/'),
        (5,'@I5@',5,'Sue','Example','Sue 4','F','Sue /Example/');
      INSERT INTO families(id,gedcom_xref) VALUES(2,'@F2@');
      INSERT INTO family_members(family_id,person_id,role) VALUES(2,4,'Husband'),(2,5,'Wife');
    """)
    db.commit()
    r=answer_question(db,'Who did Sue Knuckey marry?')
    from reunion_companion.companion.ffd_relationship_questions import _identity_choice_sort_key
    assoc=[c for c in sorted(r['choices'],key=_identity_choice_sort_key) if c['identity_group_rank']>=2]
    assert assoc[0]['person']['display_name']=='Susan Lee Jones'
    assert assoc[0]['identity_match_kind']=='given-variant-spouse-surname'


def test_question_without_residence_does_not_fabricate_residence_relevance(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    db.execute("DELETE FROM events WHERE person_id=2 AND lower(event_type)='residence'")
    db.commit()
    r=answer_question(db,'Where did Susan Knuckey live?')
    assoc=next(c for c in r['choices'] if c['person']['id']==2)
    assert assoc['question_relevant'] is False


def test_qa_pass3_best_likely_lane_precedes_recorded_name_lane(tmp_path,monkeypatch):
    monkeypatch.setenv('HOME',str(tmp_path))
    db=connect(tmp_path/'x.sqlite3');seed_many_susan_knuckeys(db)
    html=render_get(db,'/search',{'q':'Where did Susan Knuckey live?'})
    assert 'Best likely matches' in html
    assert 'People recorded with this name' in html
    assert html.index('Best likely matches') < html.index('People recorded with this name')
    best=html[html.index('Best likely matches'):html.index('People recorded with this name')]
    assert 'Susan Lee Jones' in best
    assert 'Kym Wayne Knuckey' in best


def test_qa_pass3_plain_name_uses_best_likely_lane(tmp_path,monkeypatch):
    monkeypatch.setenv('HOME',str(tmp_path))
    db=connect(tmp_path/'x.sqlite3');seed(db)
    html=render_get(db,'/search',{'q':'Susan Knuckey'})
    assert html.index('Best likely matches') < html.index('People recorded with this name')
    best=html[html.index('Best likely matches'):html.index('People recorded with this name')]
    assert 'Susan Lee Jones' in best
    assert 'Kym Wayne Knuckey' in best


def test_qa_pass3_launcher_about_uses_authoritative_release_identity():
    from pathlib import Path
    path=Path(__file__).resolve().parents[1]/"macos_app"/"build_app.py"
    source=path.read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.10 — Multi-page PDF Reproduction QA Pass 1"' in source
    assert '.replace("__APP_RELEASE__",APP_RELEASE)' in source
    assert 'a.informativeText="__APP_RELEASE__\\nGenealogy Engine: __ENGINE_BASELINE__"' in source
    assert 'RC1.0.5 — Application Identity & Distribution Polish — Visual QA Pass 2' not in source


def _choice_signature(result):
    from reunion_companion.companion.ffd_relationship_questions import _identity_choice_sort_key
    return [
        (c['person']['id'], c.get('identity_match_kind'), c.get('identity_group_rank'), c.get('identity_reason'))
        for c in sorted(result.get('choices', []), key=_identity_choice_sort_key)
    ]


def test_qa_pass4_explicit_name_uses_same_candidates_with_or_without_current_focus(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed_many_susan_knuckeys(db)
    q='Where did Susan Knuckey live?'
    search_entry=answer_question(db,q,None)
    ask_entry=answer_question(db,q,1)
    assert search_entry['kind']=='identity-choice'
    assert ask_entry['kind']=='identity-choice'
    assert _choice_signature(ask_entry)==_choice_signature(search_entry)
    assert any(c['person']['id']==2 and 'Kym Wayne Knuckey' in c['identity_reason'] for c in ask_entry['choices'])


def test_qa_pass4_marriage_question_uses_same_candidates_with_or_without_current_focus(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed_many_susan_knuckeys(db)
    q='Who did Susan Knuckey marry?'
    search_entry=answer_question(db,q,None)
    ask_entry=answer_question(db,q,1)
    assert _choice_signature(ask_entry)==_choice_signature(search_entry)


def test_qa_pass4_ask_page_uses_same_identity_lanes_as_search(tmp_path,monkeypatch):
    monkeypatch.setenv('HOME',str(tmp_path))
    db=connect(tmp_path/'x.sqlite3');seed_many_susan_knuckeys(db)
    # Add a low-information spouse-surname association so the third lane is
    # present at both entry points, mirroring real Reunion legacy-name data.
    db.executescript("""
      INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES
        (40,'@I40@',40,'Robert','Knuckey','Robert Knuckey','M','Robert /Knuckey/'),
        (41,'@I41@',41,'Susan','Example','Sue','F','Susan /Example/');
      INSERT INTO families(id,gedcom_xref) VALUES(40,'@F40@');
      INSERT INTO family_members(family_id,person_id,role) VALUES(40,40,'Husband'),(40,41,'Wife');
    """)
    db.commit()
    q='Where did Susan Knuckey live?'
    search_html=render_get(db,'/search',{'q':q})
    ask_html=render_get(db,'/questions',{'person':'1','q':q})
    for label in ('Best likely matches','People recorded with this name','Other family/name associations'):
        assert label in search_html
        assert label in ask_html
    assert 'Susan Lee Jones' in ask_html
    assert 'Kym Wayne Knuckey' in ask_html
    assert 'More people recorded with this name' in ask_html
    assert 'Answer using this person' in ask_html


def test_qa_pass4_launcher_about_uses_current_release_identity():
    from pathlib import Path
    path=Path(__file__).resolve().parents[1]/'macos_app'/'build_app.py'
    source=path.read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.10 — Multi-page PDF Reproduction QA Pass 1"' in source
    assert '.replace("__APP_RELEASE__",APP_RELEASE)' in source
