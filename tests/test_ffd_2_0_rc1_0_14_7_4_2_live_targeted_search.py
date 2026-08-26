import json

from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_targeted_bootstrap import (
    _is_placeholder_name,
    desired_searches,
    live_targeted_search,
    populate_targeted_queue,
)
from reunion_companion.companion.ryerson_surname_bootstrap import (
    _surname_form_javascript,
    harvest_surname,
)


def add_person(db,pid,surname,given):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,"
        "display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,f"@I{pid}@",pid,given,surname,f"{given} {surname}","U",f"{given} /{surname}/"),
    )


def test_placeholder_names_are_excluded(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Smith","Unknown")
    add_person(db,2,"Unknown","John")
    add_person(db,3,"Smith","John")
    db.commit()
    rows=desired_searches(db)
    assert len(rows)==1
    assert rows[0]["search_key"]=="name:smith|john"
    assert _is_placeholder_name("Unknown") is True
    assert _is_placeholder_name("John") is False


def test_public_form_builder_accepts_optional_given_name():
    js=_surname_form_javascript("Smith","John")
    assert '"Smith"' in js
    assert '"John"' in js
    assert "gn.value" in js


def test_identity_aware_harvest_writes_directly_to_target_cache(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.db")

    import reunion_companion.companion.ryerson_surname_bootstrap as mod

    row={
        "source_record_name":"JOHN SMITH",
        "event_type":"Death",
        "event_date":"01JAN2000",
        "publication":"Test Paper",
        "publication_date":"02JAN2000",
        "details":"",
        "birth_date_claim":None,
        "place_claim":None,
        "evidence_type":"death_notice",
    }

    monkeypatch.setattr(mod,"submit_surname_search",lambda *a,**k:("https://example/results","html"))
    monkeypatch.setattr(mod,"parse_ryerson_results",lambda html:[row])
    monkeypatch.setattr(mod,"_rows_correspond_to_surname",lambda rows,surname:True)
    monkeypatch.setattr(mod,"pagination_links",lambda:[])
    monkeypatch.setattr(mod,"_select_forward_pagination_link",lambda *a,**k:None)

    result=harvest_surname(
        db,"Smith",
        harvest_kind="surname_given",
        harvest_value="Smith|John",
        progress_key="name:smith|john",
        enabled_fn=lambda db:True,
    )

    assert result["unique_cached"]==1
    cache=db.execute(
        "SELECT harvest_kind,harvest_value FROM companion_external_notice_cache"
    ).fetchone()
    assert cache["harvest_kind"]=="surname_given"
    assert cache["harvest_value"]=="Smith|John"

    progress=db.execute(
        "SELECT surname_key,is_complete FROM companion_ryerson_surname_progress"
    ).fetchone()
    assert progress["surname_key"]=="name:smith|john"
    assert progress["is_complete"]==1


def test_targeted_and_broad_cache_identities_do_not_collide(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.db")
    import reunion_companion.companion.ryerson_surname_bootstrap as mod

    counter={"n":0}
    def parsed(html):
        counter["n"]+=1
        return [{
            "source_record_name":f"JOHN SMITH {counter['n']}",
            "event_type":"Death","event_date":"01JAN2000",
            "publication":"Test","publication_date":"02JAN2000",
            "details":"","birth_date_claim":None,"place_claim":None,
            "evidence_type":"death_notice",
        }]

    monkeypatch.setattr(mod,"submit_surname_search",lambda *a,**k:("https://example/results","html"))
    monkeypatch.setattr(mod,"parse_ryerson_results",parsed)
    monkeypatch.setattr(mod,"_rows_correspond_to_surname",lambda rows,surname:True)
    monkeypatch.setattr(mod,"pagination_links",lambda:[])
    monkeypatch.setattr(mod,"_select_forward_pagination_link",lambda *a,**k:None)

    harvest_surname(db,"Smith",enabled_fn=lambda db:True)
    harvest_surname(
        db,"Smith",
        harvest_kind="surname_given",
        harvest_value="Smith|John",
        progress_key="name:smith|john",
        enabled_fn=lambda db:True,
    )

    rows=db.execute(
        "SELECT harvest_kind,harvest_value FROM companion_external_notice_cache "
        "ORDER BY harvest_kind"
    ).fetchall()
    assert {(r["harvest_kind"],r["harvest_value"]) for r in rows}=={
        ("surname","Smith"),("surname_given","Smith|John")
    }
