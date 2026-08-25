from reunion_companion.companion.ryerson_surname_bootstrap import (
    _pagination_control_javascript,
    _page_record_keys,
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

def test_pagination_control_targets_numeric_page():
    js=_pagination_control_javascript(2)
    assert '"2"' in js
    assert "el.click()" in js
    assert "querySelectorAll" in js

def test_pagination_control_never_assigns_location_href():
    js=_pagination_control_javascript(2)
    assert "location.href=" not in js

def test_distinct_page_identity_model():
    page1=_page_record_keys([
        notice("A SHEARER","01JAN2000"),
        notice("B SHEARER","02JAN2000"),
    ])
    page2=_page_record_keys([
        notice("C SHEARER","03JAN2000"),
    ])
    assert page2-page1

def test_repeated_page_identity_model():
    page1=_page_record_keys([notice("A SHEARER","01JAN2000")])
    page2=_page_record_keys([notice("A SHEARER","01JAN2000")])
    assert not (page2-page1)

