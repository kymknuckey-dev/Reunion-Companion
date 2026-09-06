"""Compatibility regressions for the .12.8.1 national-search correction.

.12.8.2 supersedes only the mistaken family-wide queue rewind from .12.8.1;
the all-states form reset remains part of the live contract.
"""

from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_adapter import DEFAULT_STATE
from reunion_companion.companion.ryerson_surname_bootstrap import _surname_form_javascript
from reunion_companion.companion.ryerson_targeted_bootstrap import ensure_targeted_schema, targeted_form_javascript


def test_all_discovery_paths_reset_state_to_national():
    assert DEFAULT_STATE == ''
    for js in (_surname_form_javascript('Knuckey'), targeted_form_javascript('Rigg','Peter')):
        assert '[name="search_st"]' in js
        assert 'selectedIndex=0' in js
        assert 'st.value=all.value' in js


def test_12_8_2_restores_mistaken_family_wide_rewind(tmp_path):
    db=connect(tmp_path/'x.db')
    ensure_targeted_schema(db)
    db.execute("DELETE FROM meta WHERE key='ryerson_targeted_rewind_restored_v2'")
    db.execute("INSERT INTO companion_ryerson_targeted_queue(search_kind,surname,given_name,search_key,status,attempts,result_count,match_count,coverage_scope) VALUES('name','Rigg','Peter','name:rigg|peter','queued',0,2,1,'legacy_sa')")
    db.execute("INSERT INTO companion_external_evidence(person_gedcom_xref,source_name,evidence_type,review_status) VALUES('@I1@','Ryerson','death_notice','accepted')")
    db.commit()
    ensure_targeted_schema(db)
    row=db.execute("SELECT * FROM companion_ryerson_targeted_queue WHERE search_key='name:rigg|peter'").fetchone()
    assert row['status']=='completed'
    assert row['coverage_scope']=='legacy_sa'
    assert db.execute("SELECT review_status FROM companion_external_evidence WHERE person_gedcom_xref='@I1@'").fetchone()['review_status']=='accepted'
