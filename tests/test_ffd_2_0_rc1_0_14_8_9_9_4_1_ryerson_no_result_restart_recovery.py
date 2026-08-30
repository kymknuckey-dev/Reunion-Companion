from datetime import datetime, timedelta, timezone
import json

from reunion_companion.companion import ryerson_safari_transport as transport
from reunion_companion.companion.external_research_runner import recover_interrupted_runner_state
from reunion_companion.companion.ryerson_adapter import RyersonQuery
from reunion_companion.companion.database import connect


def test_explicit_zero_result_page_is_not_transient():
    html="<html><body><form><label>Surname</label><label>Any Given Name(s)</label></form><h2>0 notices found</h2><p>No results found</p></body></html>"
    assert transport._ryerson_page_is_no_results(html)
    assert not transport._ryerson_timeout_is_transient(html)


def test_safari_fetch_returns_explicit_zero_result_without_timeout(monkeypatch):
    form_html="<html><body><form><label>Surname</label><input name='search_sn'><label>Any Given Name(s)</label><input name='search_gn'></form></body></html>"
    zero_html="<html><body><form><label>Surname</label><label>Any Given Name(s)</label></form><h2>0 notices found</h2><p>No results found</p></body></html>"
    snapshots=iter([
        (transport.RYERSON_SEARCH_URL, form_html),
        (transport.RYERSON_SEARCH_URL, zero_html),
    ])
    monkeypatch.setattr(transport,"_safari_open",lambda *a,**k: None)
    monkeypatch.setattr(transport,"_safari_snapshot",lambda *a,**k: next(snapshots))
    monkeypatch.setattr(transport,"_safari_do_javascript",lambda *a,**k: json.dumps({"status":"submitted"}))
    status,html=transport.safari_fetch(
        RyersonQuery(surname="Schapel",given_names="Ernest",state="SA"),
        sleep=lambda _s:None,
        timeout_seconds=1.0,
        poll_seconds=0.0,
    )
    assert status==200
    assert "No results found" in html


def test_restart_recovery_requeues_searching_and_only_expired_retry_wait(tmp_path):
    db=connect(tmp_path/"x.sqlite3")
    now=datetime(2026,8,30,2,0,tzinfo=timezone.utc)
    old=(now-timedelta(hours=1)).isoformat()
    future=(now+timedelta(hours=1)).isoformat()
    rows=[
        ("@A@","A Person","searching",1,None),
        ("@B@","B Person","retry_wait",2,old),
        ("@C@","C Person","retry_wait",2,future),
        ("@D@","D Person","succeeded_no_match",1,None),
    ]
    for xref,name,status,attempts,next_retry in rows:
        db.execute(
            "INSERT INTO companion_external_scan_queue(source_name,person_gedcom_xref,person_name_snapshot,status,attempts,next_retry_at) VALUES('Ryerson',?,?,?,?,?)",
            (xref,name,status,attempts,next_retry),
        )
    db.commit()

    assert recover_interrupted_runner_state(db,now=now)==2
    got={r["person_gedcom_xref"]:r for r in db.execute("SELECT * FROM companion_external_scan_queue WHERE person_gedcom_xref IN ('@A@','@B@','@C@','@D@')")}
    assert got["@A@"]["status"]=="queued"
    assert got["@A@"]["attempts"]==0
    assert got["@B@"]["status"]=="queued"
    assert got["@C@"]["status"]=="retry_wait"
    assert got["@D@"]["status"]=="succeeded_no_match"
