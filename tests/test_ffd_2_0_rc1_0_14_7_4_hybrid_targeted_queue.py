from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_targeted_bootstrap import (
    cache_identity_for_search,configured_core_surnames,desired_searches,
    first_given_name,populate_targeted_queue,search_key,set_core_surnames,
    start_targeted_bootstrap
)

def add_person(db,pid,surname,given):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,"
        "display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,f"@I{pid}@",pid,given,surname,f"{given} {surname}","U",f"{given} /{surname}/"),
    )

def test_first_given_name_partition():
    assert first_given_name("John William")=="John"
    assert first_given_name("  Mary   Ann ")=="Mary"

def test_knuckey_is_seeded_as_core_surname(tmp_path):
    db=connect(tmp_path/"x.db")
    assert configured_core_surnames(db)==["Knuckey"]

def test_core_surname_is_one_broad_search(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Knuckey","John")
    add_person(db,2,"Knuckey","William")
    add_person(db,3,"Knuckey","John")
    db.commit()
    rows=desired_searches(db)
    assert len(rows)==1
    assert rows[0]["search_kind"]=="surname"
    assert rows[0]["people_count"]==3

def test_non_core_surname_is_partitioned_by_first_name(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Smith","John William")
    add_person(db,2,"Smith","John Peter")
    add_person(db,3,"Smith","Mary")
    db.commit()
    rows=desired_searches(db)
    assert len(rows)==2
    john=next(x for x in rows if x["given_name"]=="John")
    assert john["people_count"]==2

def test_search_identity_is_stable_and_distinct():
    assert search_key("surname","Knuckey")=="surname:knuckey"
    assert search_key("name","Smith","John")=="name:smith|john"
    assert search_key("name","Smith","Mary")=="name:smith|mary"

def test_queue_population_deduplicates_shared_first_names(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Smith","John")
    add_person(db,2,"Smith","John James")
    add_person(db,3,"Smith","Mary")
    db.commit()
    result=populate_targeted_queue(db)
    assert result["desired"]==2
    assert result["added"]==2

def test_core_surnames_are_configurable(tmp_path):
    db=connect(tmp_path/"x.db")
    set_core_surnames(db,["Knuckey","Schapel","knuckey"])
    assert configured_core_surnames(db)==["Knuckey","Schapel"]

def test_start_targeted_disables_old_surname_bootstrap(tmp_path):
    db=connect(tmp_path/"x.db")
    db.execute(
        "INSERT OR REPLACE INTO meta(key,value) "
        "VALUES('ryerson_surname_bootstrap_enabled','1')"
    )
    add_person(db,1,"Smith","John")
    db.commit()
    result=start_targeted_bootstrap(db)
    old=db.execute(
        "SELECT value FROM meta WHERE key='ryerson_surname_bootstrap_enabled'"
    ).fetchone()["value"]
    assert old=="0"
    assert result["enabled"] is True
    assert result["total"]==1

def test_targeted_cache_identity():
    assert cache_identity_for_search(
        {"search_kind":"surname","surname":"Knuckey","given_name":""}
    )=={"harvest_kind":"surname","harvest_value":"Knuckey"}
    assert cache_identity_for_search(
        {"search_kind":"name","surname":"Smith","given_name":"John"}
    )=={"harvest_kind":"surname_given","harvest_value":"Smith|John"}
