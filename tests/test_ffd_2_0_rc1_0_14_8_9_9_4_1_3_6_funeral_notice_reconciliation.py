from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence import add_external_evidence
from reunion_companion.companion.ryerson_discovery_review import (
    discoveries_for_person,
    discovery_fact_present_in_reunion,
    reconcile_waiting_discoveries,
    remember_discovery,
    set_discovery_state,
)
from reunion_companion.companion.ryerson_person_finding_bridge import (
    materialize_person_level_ryerson_findings,
)


def _person(db):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) "
        "VALUES(1,'@I1@',1,'Graham Robert','Shearer','Graham Robert Shearer','M','Graham Robert /Shearer/')"
    )
    db.execute("INSERT INTO events(person_id,event_type,date_text) VALUES(1,'Birth','3 JUN 1939')")
    db.execute("INSERT INTO events(person_id,event_type,date_text) VALUES(1,'Death','5 JUN 2015')")
    db.commit()


def _funeral_finding(db):
    return add_external_evidence(
        db,
        person_gedcom_xref='@I1@',
        person_name_snapshot='Graham Robert Shearer',
        source_name='Ryerson',
        evidence_type='funeral_notice',
        source_record_name='Graham Robert SHEARER',
        event_type='Publication',
        event_date='11JUN2015',
        publication='Adelaide Advertiser',
        publication_date='11JUN2015',
        details=None,
        birth_date_claim=None,
        place_claim=None,
        match_confidence=75,
        match_reason='surname exact; full name exact',
        review_status='new',
    )


def test_funeral_notice_publication_date_does_not_materialise_as_second_death(tmp_path):
    db=connect(tmp_path/'x.db')
    _person(db)
    _funeral_finding(db)

    materialize_person_level_ryerson_findings(db,'@I1@')
    rows=discoveries_for_person(db,1)
    assert len(rows)==1
    assert rows[0]['proposed_fact_key']==''


def test_legacy_funeral_notice_death_key_confirms_as_evidence_only(tmp_path):
    db=connect(tmp_path/'x.db')
    _person(db)
    evidence_id=_funeral_finding(db)

    row=remember_discovery(
        db,
        person_id=1,
        source_name='Ryerson',
        external_record_key=f"ryerson:{evidence_id}",
        proposed_fact_key='death:11JUN2015',
    )
    set_discovery_state(db,row['id'],'waiting_for_reunion')

    confirmed=reconcile_waiting_discoveries(
        db,
        lambda candidate: discovery_fact_present_in_reunion(db,candidate),
        now='2026-08-31T00:00:00+00:00',
    )
    assert confirmed == [row['id']]
    final=db.execute(
        "SELECT state FROM companion_external_discovery_review WHERE id=?",
        (row['id'],),
    ).fetchone()
    assert final['state']=='confirmed_complete'
