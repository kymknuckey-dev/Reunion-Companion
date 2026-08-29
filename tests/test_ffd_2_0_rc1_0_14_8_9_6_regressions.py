import pytest

from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence_scan import SourceSearchError
from reunion_companion.companion import ryerson_surname_bootstrap as ryerson
from reunion_companion.companion.ffd_relationship_questions import answer_question
from test_ffd_1_8_build1_1_query_consistency_hardening import seed, add_person


def test_verified_explicit_ryerson_no_result_is_success(monkeypatch):
    html = """
    <html><body>
      <h1>Ryerson Index</h1>
      <div class='search-results'>No records found</div>
    </body></html>
    """
    monkeypatch.setattr(ryerson, "_safari_snapshot", lambda: ("https://ryersonindex.org/search.php", html))
    monkeypatch.setattr(ryerson.time, "sleep", lambda _seconds: None)
    url, returned = ryerson._wait_for_results(expected_surname="Martin", timeout_seconds=0.1, poll_seconds=0)
    assert url.endswith("search.php")
    assert "No records found" in returned
    assert ryerson.parse_ryerson_results(returned) == []


def test_zero_rows_without_explicit_no_result_still_times_out(monkeypatch):
    html = "<html><body><h1>Ryerson Index search</h1><form></form></body></html>"
    monkeypatch.setattr(ryerson, "_safari_snapshot", lambda: ("https://ryersonindex.org/search.php", html))
    monkeypatch.setattr(ryerson.time, "sleep", lambda _seconds: None)
    ticks=iter((0.0, 0.0, 0.2, 0.2))
    monkeypatch.setattr(ryerson.time, "monotonic", lambda: next(ticks, 0.2))
    with pytest.raises(SourceSearchError, match="last parsed row count=0"):
        ryerson._wait_for_results(expected_surname="Martin", timeout_seconds=0.1, poll_seconds=0)



def test_long_spouse_end_relationship_gets_friendly_primary_answer_and_keeps_path(tmp_path):
    db=connect(tmp_path/'x')
    seed(db)
    add_person(db,10,'Mary Example','F')
    db.execute("INSERT INTO families(id,gedcom_xref) VALUES(5,'@F5@')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(5,8,'husband')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(5,10,'wife')")
    db.commit()
    r=answer_question(db,'How is Kym Wayne Knuckey related to Mary Example?',3)
    assert r['status']=='ok'
    assert r['kind']=='connection'
    assert r['answer']=="Mary Example is the wife of Kym Wayne Knuckey’s great-uncle, Lionel George Waight."
    assert r['path']
    assert r['path'][-1]['person']['display_name']=='Mary Example'
    assert r['path'][-1]['edge']=='spouse'


def test_removed_cousin_wording_is_conversational():
    from reunion_companion.companion.ffd_relationship_questions import _friendly_kinship_label
    assert _friendly_kinship_label('3rd cousin, 1 time removed')=='3rd cousin once removed'
    assert _friendly_kinship_label('2nd cousin, 2 times removed')=='2nd cousin twice removed'


def test_long_spouse_start_relationship_gets_reciprocal_friendly_answer_and_keeps_path(tmp_path):
    db=connect(tmp_path/'x')
    seed(db)
    add_person(db,10,'Mary Example','F')
    db.execute("INSERT INTO families(id,gedcom_xref) VALUES(5,'@F5@')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(5,8,'husband')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(5,10,'wife')")
    db.commit()
    r=answer_question(db,'How is Mary Example related to Kym Wayne Knuckey?',10)
    assert r['status']=='ok'
    assert r['kind']=='connection'
    assert r['answer']=="Mary Example is related to Kym Wayne Knuckey through husband Lionel George Waight. Lionel George Waight is Kym Wayne Knuckey’s great-uncle."
    assert r['path']
    assert r['path'][0]['person']['display_name']=='Mary Example'
    assert r['path'][1]['person']['display_name']=='Lionel George Waight'
    assert r['path'][1]['edge']=='spouse'


def _add_spouse_pair(db,family_id,left_id,left_role,right_id,right_role):
    db.execute("INSERT INTO families(id,gedcom_xref) VALUES(?,?)",(family_id,f'@F{family_id}@'))
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,?)",(family_id,left_id,left_role))
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,?)",(family_id,right_id,right_role))


def test_spouse_at_both_ends_gets_generalised_friendly_answer(tmp_path):
    db=connect(tmp_path/'x')
    seed(db)
    add_person(db,10,'Susan Example','F')
    add_person(db,11,'Mary Example','F')
    _add_spouse_pair(db,5,3,'husband',10,'wife')       # Kym + Susan
    _add_spouse_pair(db,6,8,'husband',11,'wife')       # Lionel + Mary
    db.commit()
    r=answer_question(db,'How is Susan Example related to Mary Example?',10)
    assert r['status']=='ok'
    assert r['kind']=='connection'
    assert r['answer']==(
        "Susan Example is related to Mary Example through their spouses. "
        "Susan Example’s husband is Kym Wayne Knuckey. "
        "Mary Example’s husband is Lionel George Waight. "
        "Lionel George Waight is Kym Wayne Knuckey’s great-uncle."
    )
    assert r['path'][1]['edge']=='spouse'
    assert r['path'][-1]['edge']=='spouse'


def test_spouse_at_both_ends_reverse_direction_is_also_friendly(tmp_path):
    db=connect(tmp_path/'x')
    seed(db)
    add_person(db,10,'Susan Example','F')
    add_person(db,11,'Mary Example','F')
    _add_spouse_pair(db,5,3,'husband',10,'wife')
    _add_spouse_pair(db,6,8,'husband',11,'wife')
    db.commit()
    r=answer_question(db,'How is Mary Example related to Susan Example?',11)
    assert r['status']=='ok'
    assert r['kind']=='connection'
    assert r['answer'].startswith('Mary Example is related to Susan Example through their spouses.')
    assert 'Mary Example’s husband is Lionel George Waight.' in r['answer']
    assert 'Susan Example’s husband is Kym Wayne Knuckey.' in r['answer']
    assert 'Kym Wayne Knuckey is Lionel George Waight’s great-nephew.' in r['answer']
    assert r['path'][1]['edge']=='spouse'
    assert r['path'][-1]['edge']=='spouse'
