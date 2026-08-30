from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_discovery_review import remember_discovery
from reunion_companion.companion.ryerson_discovery_assembly import assemble_discoveries
from reunion_companion.companion.ryerson_discovery_ui import sort_grouped_people_recent


def add_person(db,pid,name):
    bits=name.split()
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (pid,f"@I{pid}@",pid," ".join(bits[:-1]),bits[-1],name,"U",name),
    )
    db.commit()


def test_review_schema_migrates_and_rediscovery_updates_confidence_without_losing_state(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Peter Charles Mitchell")
    row=remember_discovery(db,person_id=1,source_name="Ryerson",external_record_key="ryerson:1",proposed_fact_key="death:2020-01-01")
    db.execute("UPDATE companion_external_discovery_review SET state='deferred', decision_note='keep' WHERE id=?",(row['id'],))
    db.commit()
    row=remember_discovery(db,person_id=1,source_name="Ryerson",external_record_key="ryerson:1",proposed_fact_key="death:2020-01-01",match_confidence=100)
    assert row['match_confidence']==100
    assert row['state']=='deferred'
    assert row['decision_note']=='keep'


def test_assembly_carries_match_confidence_into_review_index(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Peter Charles Mitchell")
    import reunion_companion.companion.external_evidence_matcher as matcher
    monkeypatch.setattr(matcher,"ryerson_death_candidates",lambda db:[{"person_id":1}])
    result=assemble_discoveries(db,[{
        "person_id":1,"notice_id":"peter-100","death_date":"2020-01-01",
        "match_status":"candidate","match_confidence":100,
    }])
    assert result['assembled_count']==1
    row=db.execute("SELECT * FROM companion_external_discovery_review WHERE person_id=1").fetchone()
    assert row['match_confidence']==100


def test_recent_sort_uses_confidence_stored_on_review_candidates():
    peter={"person_id":1,"display_name":"Peter Charles Mitchell","proposed_fact_key":"death:2010-01-01","match_confidence":100}
    newer={"person_id":2,"display_name":"Newer Name Match","proposed_fact_key":"death:2025-01-01","match_confidence":75}
    ordered=sort_grouped_people_recent([(2,[newer]),(1,[peter])])
    assert [pid for pid,_ in ordered]==[1,2]
