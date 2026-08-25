import json

from reunion_companion.companion.ryerson_safari_harvest import (
    _annual_form_javascript,
    _page_number_from_link,
    _pagination_javascript,
)


def test_annual_search_uses_confirmed_live_fields():
    js=_annual_form_javascript("Adelaide",2021)
    assert '[name="search_lo"]' in js
    assert '[name="search_y1"]' in js
    assert '[name="search_y2"]' in js
    assert '[name="search"][type="submit"]' in js
    assert json.dumps("Adelaide") in js
    assert json.dumps("2021") in js


def test_annual_search_sets_same_start_and_end_year():
    js=_annual_form_javascript("Adelaide",2026)
    assert "y1.value" in js
    assert "y2.value" in js
    assert js.count('"2026"') >= 1


def test_pagination_probe_is_anchor_only_and_conservative():
    js=_pagination_javascript()
    assert "querySelectorAll('a[href]')" in js
    assert "button" not in js.lower()
    assert "form.submit" not in js.lower()


def test_numeric_page_text_becomes_page_number():
    assert _page_number_from_link("2","https://example.test/results?page=2",9)==2


def test_page_query_parameter_is_recognised():
    assert _page_number_from_link("Next","https://example.test/results?page=7",9)==7


def test_unknown_pagination_uses_fallback():
    assert _page_number_from_link("Next","https://example.test/results?foo=bar",4)==4
