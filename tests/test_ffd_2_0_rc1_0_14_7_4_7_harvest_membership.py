from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_harvest import (
    cache_harvest_rows,
    harvest_membership_count,
)

def notice(name):
    return {
        "source_record_name":name,
        "event_type":"Death",
        "event_date":"01JAN2000",
        "publication":"Test Paper",
        "publication_date":"02JAN2000",
        "details":"",
        "birth_date_claim":None,
        "place_claim":None,
        "evidence_type":"death_notice",
    }

def test_same_notice_can_belong_to_broad_and_targeted_search(tmp_path):
    db=connect(tmp_path/"x.db")
    row=notice("JOHN MITCHELL")
    first=cache_harvest_rows(
        db,[row],harvest_kind="surname",harvest_value="Mitchell",
        harvest_year=0,page_number=1,
    )
    second=cache_harvest_rows(
        db,[row],harvest_kind="surname_given",harvest_value="Mitchell|John",
        harvest_year=0,page_number=1,
    )
    cached=db.execute(
        "SELECT COUNT(*) FROM companion_external_notice_cache WHERE source_name='Ryerson'"
    ).fetchone()[0]
    assert cached==1
    assert harvest_membership_count(
        db,harvest_kind="surname",harvest_value="Mitchell"
    )==1
    assert harvest_membership_count(
        db,harvest_kind="surname_given",harvest_value="Mitchell|John"
    )==1
    assert first["inserted"]==1
    assert second["existing"]==1
    assert second["membership_count"]==1

def test_targeted_membership_counts_existing_master_rows(tmp_path):
    db=connect(tmp_path/"x.db")
    rows=[notice("JOHN MITCHELL"),notice("JOHN A MITCHELL")]
    cache_harvest_rows(
        db,rows,harvest_kind="surname",harvest_value="Mitchell",
        harvest_year=0,page_number=1,
    )
    result=cache_harvest_rows(
        db,rows,harvest_kind="surname_given",harvest_value="Mitchell|John",
        harvest_year=0,page_number=1,
    )
    assert result["inserted"]==0
    assert result["existing"]==2
    assert result["membership_count"]==2

def test_membership_is_idempotent_across_repeat_page_processing(tmp_path):
    db=connect(tmp_path/"x.db")
    row=notice("JOHN MITCHELL")
    for _ in range(2):
        cache_harvest_rows(
            db,[row],harvest_kind="surname_given",harvest_value="Mitchell|John",
            harvest_year=0,page_number=2,
        )
    assert harvest_membership_count(
        db,harvest_kind="surname_given",harvest_value="Mitchell|John"
    )==1
