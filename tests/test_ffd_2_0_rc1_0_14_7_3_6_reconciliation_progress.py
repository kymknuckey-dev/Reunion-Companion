from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_harvest import cache_harvest_rows
from reunion_companion.companion.ryerson_surname_bootstrap import (
    _save_progress,
    enqueue_unique_surnames,
    reconcile_cached_surnames,
    reconcile_cached_surnames_detail,
    start_bootstrap,
)

def person(db,pid,xref,given,surname):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,xref,pid,given,surname,f"{given} {surname}","M",f"{given} /{surname}/"),
    )

def notice(name,date):
    return {
        "evidence_type":"death_notice",
        "source_record_name":name,
        "event_type":"Death",
        "event_date":date,
        "publication":"Test Paper",
        "publication_date":date,
        "details":None,
        "birth_date_claim":None,
        "place_claim":None,
    }

def test_cached_surname_without_progress_is_reconciled(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Peter","Rigg")
    db.commit()
    enqueue_unique_surnames(db)
    cache_harvest_rows(db,[notice("Peter RIGG","02JAN2021")],harvest_kind="surname",harvest_value="Rigg",harvest_year=0)
    assert reconcile_cached_surnames(db)==1
    row=db.execute("SELECT status,result_count FROM companion_ryerson_surname_queue WHERE surname_key='rigg'").fetchone()
    assert row["status"]=="completed"
    assert row["result_count"]==1

def test_incomplete_progress_blocks_cache_reconciliation(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Test","Shearer")
    db.commit()
    enqueue_unique_surnames(db)
    cache_harvest_rows(db,[notice("A SHEARER","01JAN2000")],harvest_kind="surname",harvest_value="Shearer",harvest_year=0)
    _save_progress(db,"Shearer",current_page=2,current_url="https://ryersonindex.org/search.php#",pages_completed=1,rows_seen=1000,inserted_rows=1000,existing_rows=0,is_complete=False)
    assert reconcile_cached_surnames(db)==0
    row=db.execute("SELECT status FROM companion_ryerson_surname_queue WHERE surname_key='shearer'").fetchone()
    assert row["status"]=="queued"

def test_start_bootstrap_preserves_incomplete_surname(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Test","Shearer")
    db.commit()
    enqueue_unique_surnames(db)
    cache_harvest_rows(db,[notice("A SHEARER","01JAN2000")],harvest_kind="surname",harvest_value="Shearer",harvest_year=0)
    _save_progress(db,"Shearer",current_page=2,current_url="https://ryersonindex.org/search.php#",pages_completed=1,rows_seen=1000,inserted_rows=1000,existing_rows=0,is_complete=False)
    result=start_bootstrap(db)
    assert result["enabled"] is True
    assert result["reconciled_cached"]==0
    row=db.execute("SELECT status FROM companion_ryerson_surname_queue WHERE surname_key='shearer'").fetchone()
    assert row["status"]=="queued"

def test_detail_reports_protected_incomplete(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Test","Shearer")
    db.commit()
    enqueue_unique_surnames(db)
    cache_harvest_rows(db,[notice("A SHEARER","01JAN2000")],harvest_kind="surname",harvest_value="Shearer",harvest_year=0)
    _save_progress(db,"Shearer",current_page=2,current_url="#",pages_completed=1,rows_seen=1000,inserted_rows=1000,existing_rows=0,is_complete=False)
    out=reconcile_cached_surnames_detail(db)
    assert out["reconciled"]==0
    assert out["protected_incomplete"]==1
