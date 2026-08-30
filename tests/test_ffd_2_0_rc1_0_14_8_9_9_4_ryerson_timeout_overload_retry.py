import json
import pytest
from reunion_companion.companion.external_evidence_scan import SourceBusyError
from reunion_companion.companion.ryerson_adapter import RyersonQuery
from reunion_companion.companion import ryerson_safari_transport as transport

def test_timeout_classifier_recognises_explicit_overload():
    html="<html><body><h1>Server Overloaded</h1><p>Sorry, our server is feeling a bit overworked.</p></body></html>"
    assert transport._ryerson_timeout_is_transient(html)

def test_timeout_classifier_recognises_search_form_left_pending():
    html="<html><body><form><label>Surname</label><input name='search_sn'><label>Any Given Name(s)</label><input name='search_gn'></form></body></html>"
    assert transport._ryerson_timeout_is_transient(html)

def test_timeout_classifier_does_not_reclassify_unrelated_page():
    assert not transport._ryerson_timeout_is_transient("<html><body><p>Safari could not load this page.</p></body></html>")

def test_safari_result_timeout_left_on_search_form_becomes_busy(monkeypatch):
    form_html="<html><body><form><label>Surname</label><input name='search_sn'><label>Any Given Name(s)</label><input name='search_gn'></form></body></html>"
    snapshots=iter([
        (transport.RYERSON_SEARCH_URL,form_html),
        (transport.RYERSON_SEARCH_URL,form_html),
        (transport.RYERSON_SEARCH_URL,form_html),
    ])
    monkeypatch.setattr(transport,"_safari_open",lambda *a,**k: None)
    monkeypatch.setattr(transport,"_safari_snapshot",lambda *a,**k: next(snapshots))
    monkeypatch.setattr(transport,"_safari_do_javascript",lambda *a,**k: json.dumps({"status":"submitted"}))
    times=iter([0.0,0.0,0.0,2.0,2.0])
    monkeypatch.setattr(transport.time,"monotonic",lambda: next(times,2.0))
    with pytest.raises(SourceBusyError,match="did not complete; retry later"):
        transport.safari_fetch(RyersonQuery(surname="Biggs",given_names="Mary",state="SA"),sleep=lambda _s:None,timeout_seconds=1.0,poll_seconds=0.0)
