from datetime import datetime, timezone

from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence import (
    RYERSON_NATIONAL_REWIND_META,
    ensure_ryerson_national_coverage,
)
from reunion_companion.companion.external_evidence_scan import run_one_scan
from reunion_companion.companion.ryerson_adapter import DEFAULT_STATE, build_ryerson_queries
from reunion_companion.companion.ryerson_surname_bootstrap import _surname_form_javascript
from reunion_companion.companion.ryerson_targeted_bootstrap import (
    ensure_targeted_schema,
    targeted_form_javascript,
)


def _queue(db, xref, status, completed_at=None, result_count=0):
    db.execute(
        "INSERT INTO companion_external_scan_queue(source_name,person_gedcom_xref,person_name_snapshot,status,completed_at,result_count) VALUES('Ryerson',?,?,?,?,?)",
        (xref, xref, status, completed_at, result_count),
    )


def test_default_live_search_is_national():
    assert DEFAULT_STATE == ""
    assert build_ryerson_queries({"surname":"Rigg","given_names":"Peter Stanley"})[0].state == ""


def test_every_bootstrap_form_explicitly_resets_state():
    for js in (_surname_form_javascript("Knuckey"), targeted_form_javascript("Ingram","Simon")):
        assert '[name="search_st"]' in js
        assert "all states" in js.lower()
        assert "st.value=all.value" in js


def test_normal_queue_rewind_preserves_new_national_runs_and_evidence(tmp_path):
    db=connect(tmp_path/'x.db')
    # connect() has already applied the migration to an empty DB; remove the marker
    # so this test can seed a realistic pre-correction queue then apply it once.
    db.execute("DELETE FROM meta WHERE key=?",(RYERSON_NATIONAL_REWIND_META,))
    _queue(db,'@OLD1@','succeeded_with_findings','2026-08-29T01:00:00+00:00',2)
    _queue(db,'@OLD2@','succeeded_no_match','2026-08-29T02:00:00+00:00',0)
    _queue(db,'@NEW@','succeeded_with_findings','2026-09-06T01:15:00+00:00',1)
    _queue(db,'@WAIT@','queued',None,0)
    db.execute("INSERT INTO companion_external_evidence(person_gedcom_xref,source_name,evidence_type,review_status) VALUES('@OLD1@','Ryerson','death_notice','accepted')")
    db.commit()

    ensure_ryerson_national_coverage(db)
    rows={r['person_gedcom_xref']:r for r in db.execute("SELECT * FROM companion_external_scan_queue")}
    assert rows['@OLD1@']['status']=='queued'
    assert rows['@OLD1@']['coverage_scope']=='legacy_sa'
    assert rows['@OLD2@']['status']=='queued'
    assert rows['@NEW@']['status']=='succeeded_with_findings'
    assert rows['@NEW@']['coverage_scope']=='national'
    assert rows['@NEW@']['coverage_completed_at']=='2026-09-06T01:15:00+00:00'
    assert rows['@WAIT@']['coverage_scope']=='national_pending'
    ev=db.execute("SELECT review_status FROM companion_external_evidence WHERE person_gedcom_xref='@OLD1@'").fetchone()
    assert ev['review_status']=='accepted'

    # Idempotent: a second migration does not rewind the preserved national row.
    ensure_ryerson_national_coverage(db)
    assert db.execute("SELECT status FROM companion_external_scan_queue WHERE person_gedcom_xref='@NEW@'").fetchone()['status']=='succeeded_with_findings'


def test_successful_normal_scan_certifies_national_coverage(tmp_path):
    db=connect(tmp_path/'x.db')
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(1,'@I1@',1,'Kirsten','Noske','Kirsten Noske','F','Kirsten /Noske/')")
    db.execute("INSERT INTO companion_external_scan_queue(source_name,person_gedcom_xref,person_name_snapshot,status,coverage_scope) VALUES('Ryerson','@I1@','Kirsten Noske','queued','national_pending')")
    db.commit()
    now=datetime(2026,9,6,2,0,tzinfo=timezone.utc)
    result=run_one_scan(db,lambda profile: [],now=now)
    assert result['status']=='succeeded_no_match'
    row=db.execute("SELECT status,coverage_scope,coverage_completed_at FROM companion_external_scan_queue WHERE person_gedcom_xref='@I1@'").fetchone()
    assert row['status']=='succeeded_no_match'
    assert row['coverage_scope']=='national'
    assert row['coverage_completed_at']=='2026-09-06T02:00:00+00:00'


def test_mistaken_targeted_rewind_is_restored_once(tmp_path):
    db=connect(tmp_path/'x.db')
    ensure_targeted_schema(db)
    db.execute("DELETE FROM meta WHERE key='ryerson_targeted_rewind_restored_v2'")
    db.execute("INSERT INTO companion_ryerson_targeted_queue(search_kind,surname,given_name,search_key,status,coverage_scope,result_count) VALUES('name','Ingram','Simon','name:ingram|simon','queued','legacy_sa',0)")
    db.execute("INSERT INTO companion_ryerson_targeted_queue(search_kind,surname,given_name,search_key,status,coverage_scope,result_count) VALUES('name','Battye','Orvyn','name:battye|orvyn','failed','legacy_sa',0)")
    db.commit()
    ensure_targeted_schema(db)
    got={r['search_key']:r for r in db.execute("SELECT * FROM companion_ryerson_targeted_queue")}
    assert got['name:ingram|simon']['status']=='completed'
    assert got['name:battye|orvyn']['status']=='failed'
