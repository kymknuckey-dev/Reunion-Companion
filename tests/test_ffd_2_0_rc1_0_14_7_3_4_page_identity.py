from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_harvest import cache_harvest_rows
from reunion_companion.companion.ryerson_surname_bootstrap import _page_record_keys,_unique_cached_count

def notice(name,date):
    return {
        "evidence_type":"death_notice","source_record_name":name,
        "event_type":"Death","event_date":date,
        "publication":"Test Paper","publication_date":date,
        "details":None,"birth_date_claim":None,"place_claim":None,
    }

def test_page_identity_detects_repeated_page():
    a=[notice("A SHEARER","01JAN2000"),notice("B SHEARER","02JAN2000")]
    b=[notice("A SHEARER","01JAN2000"),notice("B SHEARER","02JAN2000")]
    assert _page_record_keys(b)-_page_record_keys(a)==set()

def test_page_identity_detects_new_records():
    a=[notice("A SHEARER","01JAN2000")]
    b=[notice("B SHEARER","02JAN2000")]
    assert len(_page_record_keys(b)-_page_record_keys(a))==1

def test_unique_cached_count_ignores_duplicate_harvest_rows(tmp_path):
    db=connect(tmp_path/"x.db")
    row=notice("A SHEARER","01JAN2000")
    cache_harvest_rows(db,[row],harvest_kind="surname",harvest_value="Shearer",harvest_year=0,page_number=1)
    cache_harvest_rows(db,[row],harvest_kind="surname",harvest_value="Shearer",harvest_year=0,page_number=2)
    assert _unique_cached_count(db,"Shearer")==1
