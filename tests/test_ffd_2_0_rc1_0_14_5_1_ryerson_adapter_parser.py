from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence import external_evidence_for_person
from reunion_companion.companion.external_evidence_scan import (
    SourceBusyError,
    enqueue_death_research_candidates,
    queue_rows,
    run_one_scan,
)
from reunion_companion.companion.ryerson_adapter import (
    RyersonQuery,
    build_ryerson_queries,
    logical_form_payload,
    make_ryerson_search,
    parse_ryerson_results,
    response_is_busy,
    search_ryerson,
)


HTML_HEADER = """
<table>
<tr>
<th>Surname</th><th>Given Names</th><th>Notice Type</th><th>Date</th>
<th>Event</th><th>Age</th><th>Other Details</th><th>Publication</th><th>Published</th>
</tr>
"""


def test_query_strategy_uses_first_given_name_only():
    profile={"surname":"Rigg","given_names":"Peter Stanly"}
    assert build_ryerson_queries(profile)==[
        RyersonQuery("Rigg","Peter",""),
    ]


def test_logical_payload_is_transport_independent():
    q=RyersonQuery("Howie","Rodney Thomas","SA")
    assert logical_form_payload(q)=={
        "surname":"Howie",
        "given_names":"Rodney Thomas",
        "state":"SA",
    }


def test_parser_normalises_peter_notice():
    html=HTML_HEADER+"""
<tr><td>RIGG</td><td>Peter Stanley</td><td>Death notice</td>
<td>02JAN2021</td><td>Death</td><td></td>
<td>late of Curramulka (born 21 May 1944)</td>
<td>Adelaide Advertiser</td><td>04JAN2021</td></tr></table>
"""
    rows=parse_ryerson_results(html)
    assert len(rows)==1
    r=rows[0]
    assert r["source_record_name"]=="Peter Stanley RIGG"
    assert r["event_type"]=="Death"
    assert r["event_date"]=="02JAN2021"
    assert r["publication"]=="Adelaide Advertiser"
    assert r["publication_date"]=="04JAN2021"
    assert r["birth_date_claim"]=="21 May 1944"
    assert r["place_claim"]=="Curramulka"


def test_parser_normalises_death_and_funeral_rows():
    html=HTML_HEADER+"""
<tr><td>HOWIE</td><td>Rodney Thomas</td><td>Death notice</td>
<td>09JUL2026</td><td>Death</td><td></td>
<td>(born 07 Oct 1940 Adelaide)</td>
<td>Adelaide Advertiser</td><td>11JUL2026</td></tr>
<tr><td>HOWIE</td><td>Rodney Thomas</td><td>Funeral notice</td>
<td>16JUL2026</td><td>Funeral</td><td></td><td></td>
<td>Adelaide Advertiser</td><td>11JUL2026</td></tr></table>
"""
    rows=parse_ryerson_results(html)
    assert [r["evidence_type"] for r in rows]==["death_notice","funeral_notice"]
    assert rows[0]["event_date"]=="09JUL2026"
    assert rows[1]["event_date"]=="16JUL2026"


def test_busy_detection_covers_429_and_visible_busy_message():
    assert response_is_busy(429,"")
    assert response_is_busy(200,"The server is busy. Please try again later.")
    assert not response_is_busy(200,"No records found")


def test_peter_first_name_search_can_return_correct_middle_name():
    profile={
        "surname":"Rigg",
        "given_names":"Peter Stanly",
        "display_name":"Peter Stanly Rigg",
    }
    calls=[]
    no_results="<html><body><p>No records found</p></body></html>"
    peter=HTML_HEADER+"""
<tr><td>RIGG</td><td>Peter Stanley</td><td>Death notice</td>
<td>02JAN2021</td><td>Death</td><td></td>
<td>late of Curramulka (born 21 May 1944)</td>
<td>Adelaide Advertiser</td><td>04JAN2021</td></tr></table>
"""
    def fetch(q):
        calls.append(q)
        return (200,no_results if q.given_names=="Peter Stanly" else peter)
    rows=search_ryerson(profile,fetch)
    assert len(rows)==1
    assert [q.given_names for q in calls]==["Peter"]
    assert rows[0]["source_record_name"]=="Peter Stanley RIGG"


def test_busy_on_first_query_stops_fallback_and_defers_to_queue():
    profile={"surname":"Rigg","given_names":"Peter Stanly"}
    calls=[]
    def fetch(q):
        calls.append(q)
        return 429,"Too Many Requests"
    try:
        search_ryerson(profile,fetch)
        assert False,"expected SourceBusyError"
    except SourceBusyError:
        pass
    assert len(calls)==1


def test_adapter_plugs_into_unattended_queue_and_persists_peter(tmp_path):
    db=connect(tmp_path/"x.db")
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) "
        "VALUES(1,'@I1@',1,'Peter Stanly','Rigg','Peter Stanly Rigg','M','Peter Stanly /Rigg/')"
    )
    db.execute(
        "INSERT INTO events(person_id,event_type,date_text,place_text) "
        "VALUES(1,'Birth','21 May 1944','Brighton Community Hospital')"
    )
    db.commit()
    assert enqueue_death_research_candidates(db)==1

    no_results="<html><body><p>No records found</p></body></html>"
    peter=HTML_HEADER+"""
<tr><td>RIGG</td><td>Peter Stanley</td><td>Death notice</td>
<td>02JAN2021</td><td>Death</td><td></td>
<td>late of Curramulka (born 21 May 1944)</td>
<td>Adelaide Advertiser</td><td>04JAN2021</td></tr></table>
"""
    def fetch(q):
        return (200,no_results if q.given_names=="Peter Stanly" else peter)

    result=run_one_scan(db,make_ryerson_search(fetch))
    assert result["status"]=="succeeded_with_findings"
    findings=external_evidence_for_person(db,"@I1@")
    assert len(findings)==1
    assert findings[0]["source_record_name"]=="Peter Stanley RIGG"
    assert findings[0]["event_date"]=="02JAN2021"
    assert queue_rows(db)[0]["status"]=="succeeded_with_findings"
