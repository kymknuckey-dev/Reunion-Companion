from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_discovery_review import (
    discovery_fact_present_in_reunion,
    reconcile_waiting_discoveries,
    remember_discovery,
    set_discovery_state,
)


def _person(db):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) "
        "VALUES(1,'@I1@',1,'Graham Robert','SHEARER','Graham Robert SHEARER','M','Graham Robert /SHEARER/')"
    )
    db.execute(
        "INSERT INTO events(person_id,event_type,date_text) VALUES(1,'Death','5 JUN 2015')"
    )
    db.commit()


def test_later_accepted_fact_already_in_reunion_confirms_on_next_reconciliation(tmp_path):
    db=connect(tmp_path/'x.db')
    _person(db)
    row=remember_discovery(
        db, person_id=1, source_name='Ryerson', external_record_key='later',
        proposed_fact_key='death:05JUN2015',
    )
    set_discovery_state(db,row['id'],'waiting_for_reunion')
    confirmed=reconcile_waiting_discoveries(
        db, lambda candidate: discovery_fact_present_in_reunion(db,candidate),
        now='2026-08-31T00:00:00+00:00',
    )
    assert confirmed == [row['id']]
    final=db.execute(
        "SELECT state FROM companion_external_discovery_review WHERE id=?",(row['id'],)
    ).fetchone()
    assert final['state']=='confirmed_complete'


def test_accepted_evidence_with_no_reunion_fact_does_not_wait_forever(tmp_path):
    db=connect(tmp_path/'x.db')
    _person(db)
    row=remember_discovery(
        db, person_id=1, source_name='Ryerson', external_record_key='publication-only',
        proposed_fact_key='',
    )
    set_discovery_state(db,row['id'],'waiting_for_reunion')
    confirmed=reconcile_waiting_discoveries(
        db, lambda candidate: discovery_fact_present_in_reunion(db,candidate),
        now='2026-08-31T00:00:00+00:00',
    )
    assert confirmed == [row['id']]
    final=db.execute(
        "SELECT state FROM companion_external_discovery_review WHERE id=?",(row['id'],)
    ).fetchone()
    assert final['state']=='confirmed_complete'
