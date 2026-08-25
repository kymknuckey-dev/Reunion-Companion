import json
from types import SimpleNamespace

import pytest

from reunion_companion.companion.external_evidence_scan import SourceBusyError,SourceSearchError
from reunion_companion.companion.ryerson_adapter import RyersonQuery
from reunion_companion.companion.ryerson_safari_transport import (
    BrowserTransportUnavailable,
    _form_fill_javascript,
    _run_osascript,
    safari_transport_available,
)


def completed(stdout="",stderr="",returncode=0):
    return SimpleNamespace(stdout=stdout,stderr=stderr,returncode=returncode)


def test_form_script_uses_semantic_field_discovery():
    js=_form_fill_javascript(RyersonQuery("Rigg","Peter","SA"))
    assert "surname" in js
    assert "given names" in js
    assert "state" in js
    assert "South Australia" in js or "south australia" in js
    assert "requestSubmit" in js


def test_form_script_embeds_values_safely():
    js=_form_fill_javascript(RyersonQuery("O'Neil",'Anne "Nan"',"SA"))
    assert json.dumps("O'Neil") in js
    assert json.dumps('Anne "Nan"') in js


def test_osascript_permission_error_becomes_transport_unavailable():
    def runner(*args,**kwargs):
        return completed(stderr="Safari got an error: JavaScript from Apple Events is not allowed",returncode=1)
    with pytest.raises(BrowserTransportUnavailable):
        _run_osascript("x",runner=runner)


def test_osascript_other_error_is_source_error():
    def runner(*args,**kwargs):
        return completed(stderr="some other failure",returncode=1)
    with pytest.raises(SourceSearchError):
        _run_osascript("x",runner=runner)


def test_transport_availability_reports_permission_problem():
    def runner(*args,**kwargs):
        return completed(stderr="Not authorized to send Apple events to Safari",returncode=1)
    ok,msg=safari_transport_available(runner=runner)
    assert ok is False
    assert "authorized" in msg.lower()
