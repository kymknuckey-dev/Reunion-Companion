from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_discovery_materialize import materialize_existing_ryerson_discoveries
from reunion_companion.companion.ryerson_discovery_review import discoveries_for_person, set_discovery_state



def eligible_person(db,pid,birth="1 JAN 1950"):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",(pid,f"@I{pid}@",pid,"Test",f"Person{pid}",f"Test Person{pid}","U",f"Test /Person{pid}/"))
    db.execute("INSERT INTO events(person_id,event_type,date_text,place_text,note_text) VALUES(?,?,?,?,?)",(pid,"Birth",birth,None,None))
    db.commit()

def test_raw_queue_counts_never_materialise_discoveries(tmp_path):
    db=connect(tmp_path/"x.db")
    db.execute("""
        CREATE TABLE ryerson_targeted_queue (
            search_key TEXT,
            result_count INTEGER,
            match_count INTEGER
        )
    """)
    db.execute("INSERT INTO ryerson_targeted_queue VALUES('name:mitchell|john',1556,1130)")
    db.commit()
    result=materialize_existing_ryerson_discoveries(db)
    assert result["candidate_relationships"]==0
    assert result["assembled_count"]==0


def test_concrete_person_notice_relationship_materialises(tmp_path):
    db=connect(tmp_path/"x.db")
    eligible_person(db,42)
    db.execute("""
        CREATE TABLE companion_external_notice_membership (
            person_id INTEGER,
            notice_id TEXT,
            death_date TEXT,
            match_status TEXT,
            match_reason TEXT
        )
    """)
    db.execute(
        "INSERT INTO companion_external_notice_membership VALUES(?,?,?,?,?)",
        (42,"notice-1","2021-01-02","candidate","Person/notice match"),
    )
    db.commit()
    result=materialize_existing_ryerson_discoveries(db)
    assert result["candidate_relationships"]==1
    assert result["assembled_count"]==1
    rows=discoveries_for_person(db,42)
    assert len(rows)==1
    assert rows[0]["proposed_fact_key"]=="death:2021-01-02"


def test_repeated_materialisation_preserves_review_state(tmp_path):
    db=connect(tmp_path/"x.db")
    eligible_person(db,9)
    db.execute("""
        CREATE TABLE ryerson_candidate_evidence (
            reunion_person_id INTEGER,
            external_record_key TEXT,
            match_status TEXT
        )
    """)
    db.execute("INSERT INTO ryerson_candidate_evidence VALUES(?,?,?)",(9,"abc","candidate"))
    db.commit()

    materialize_existing_ryerson_discoveries(db)
    row=discoveries_for_person(db,9)[0]
    set_discovery_state(db,row["id"],"rejected",note="Wrong person")

    materialize_existing_ryerson_discoveries(db)
    rows=discoveries_for_person(db,9)
    assert len(rows)==1
    assert rows[0]["state"]=="rejected"
    assert rows[0]["decision_note"]=="Wrong person"


def test_duplicate_relationship_across_tables_is_materialised_once(tmp_path):
    db=connect(tmp_path/"x.db")
    eligible_person(db,5)
    for table in ("ryerson_candidate_match","ryerson_notice_membership"):
        db.execute(f"""
            CREATE TABLE {table} (
                person_id INTEGER,
                notice_id TEXT,
                match_status TEXT
            )
        """)
        db.execute(f"INSERT INTO {table} VALUES(?,?,?)",(5,"same","candidate"))
    db.commit()
    result=materialize_existing_ryerson_discoveries(db)
    assert result["candidate_relationships"]==1
    assert len(discoveries_for_person(db,5))==1
