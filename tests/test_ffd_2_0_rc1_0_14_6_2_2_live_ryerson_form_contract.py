from reunion_companion.companion.ryerson_adapter import RyersonQuery
from reunion_companion.companion.ryerson_safari_transport import _form_fill_javascript


def test_live_ryerson_field_names_are_preferred():
    js=_form_fill_javascript(RyersonQuery("Rigg","Peter","SA"))
    assert '[name="search_sn"]' in js
    assert '[name="search_gn"]' in js
    assert '[name="search_st"]' in js
    assert '[name="search"][type="submit"]' in js


def test_semantic_fallbacks_are_retained():
    js=_form_fill_javascript(RyersonQuery("Howie","Rodney Thomas","SA"))
    assert "findControl(['surname'" in js
    assert "findControl(['given names'" in js
    assert "findControl(['state'])" in js


def test_known_live_values_are_embedded():
    js=_form_fill_javascript(RyersonQuery("Rigg","Peter","SA"))
    assert '"Rigg"' in js
    assert '"Peter"' in js
    assert '"SA"' in js
