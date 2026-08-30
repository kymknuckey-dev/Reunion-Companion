from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence import external_evidence_for_person
from reunion_companion.companion.ryerson_browser_assist import (
    RYERSON_SEARCH_URL,
    build_browser_search_plan,
    import_copied_ryerson_content,
    open_ryerson_search,
    parse_copied_ryerson_content,
)


def person(db,pid,xref,given,surname,display=None):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (pid,xref,pid,given,surname,display or f"{given} {surname}","M",f"{given} /{surname}/"),
    )


def event(db,pid,kind,date=None,place=None):
    db.execute(
        "INSERT INTO events(person_id,event_type,date_text,place_text) VALUES(?,?,?,?)",
        (pid,kind,date,place),
    )


def test_browser_plan_uses_same_conservative_variants():
    p={"surname":"Rigg","given_names":"Peter Stanly"}
    plan=build_browser_search_plan(p)
    assert plan.url==RYERSON_SEARCH_URL
    assert plan.searches==(
        {"surname":"Rigg","given_names":"Peter","state":"SA"},
    )


def test_open_uses_normal_browser_without_submitting_search():
    opened=[]
    plan=open_ryerson_search(
        {"surname":"Howie","given_names":"Rodney Thomas"},
        opener=lambda url: opened.append(url),
    )
    assert opened==[RYERSON_SEARCH_URL]
    assert plan.searches[0]["given_names"]=="Rodney"


def test_parse_tab_separated_peter_result():
    text=(
        "Surname\tGiven Names\tNotice Type\tDate\tEvent\tAge\tOther Details\tPublication\tPublished\n"
        "RIGG\tPeter Stanley\tDeath notice\t02JAN2021\tDeath\t\t"
        "late of Curramulka (born 21 May 1944)\tAdelaide Advertiser\t04JAN2021\n"
    )
    rows=parse_copied_ryerson_content(text)
    assert len(rows)==1
    row=rows[0]
    assert row["source_record_name"]=="Peter Stanley RIGG"
    assert row["event_date"]=="02JAN2021"
    assert row["birth_date_claim"]=="21 May 1944"
    assert row["place_claim"]=="Curramulka"


def test_parse_copied_html_uses_existing_ryerson_parser():
    html="""
    <table><tr><th>Surname</th><th>Given Names</th><th>Notice Type</th>
    <th>Date</th><th>Event</th><th>Age</th><th>Other Details</th>
    <th>Publication</th><th>Published</th></tr>
    <tr><td>HOWIE</td><td>Rodney Thomas</td><td>Death notice</td>
    <td>09JUL2026</td><td>Death</td><td></td>
    <td>(born 07 Oct 1940 Adelaide)</td><td>Adelaide Advertiser</td>
    <td>11JUL2026</td></tr></table>
    """
    rows=parse_copied_ryerson_content(html)
    assert len(rows)==1
    assert rows[0]["source_record_name"]=="Rodney Thomas HOWIE"
    assert rows[0]["event_date"]=="09JUL2026"


def test_import_peter_copy_matches_and_persists(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Peter Stanly","Rigg","Peter Stanly Rigg")
    event(db,1,"Birth","21 May 1944","Brighton Community Hospital")
    db.commit()

    text=(
        "RIGG\tPeter Stanley\tDeath notice\t02JAN2021\tDeath\t\t"
        "late of Curramulka (born 21 May 1944)\tAdelaide Advertiser\t04JAN2021"
    )
    result=import_copied_ryerson_content(db,1,text)
    assert result["status"]=="imported"
    assert result["parsed"]==1
    assert result["stored"]==1
    findings=external_evidence_for_person(db,"@I1@")
    assert len(findings)==1
    assert findings[0]["source_name"]=="Ryerson"
    assert findings[0]["event_date"]=="02JAN2021"
    assert findings[0]["match_confidence"]>=80


def test_import_conflicting_birth_date_is_rejected_and_not_stored(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","John","Smith")
    event(db,1,"Birth","01 Jan 1940","Adelaide")
    db.commit()

    text=(
        "SMITH\tJohn\tDeath notice\t01JAN2020\tDeath\t\t"
        "born 01 Jan 1955\tAdelaide Advertiser\t02JAN2020"
    )
    result=import_copied_ryerson_content(db,1,text)
    assert result["status"]=="no_accepted_findings"
    assert result["rejected"]==1
    assert external_evidence_for_person(db,"@I1@")==[]


def test_multiple_rows_can_be_imported_for_one_person(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Rodney Thomas","Howie")
    event(db,1,"Birth","07 Oct 1940","Adelaide")
    db.commit()

    text=(
        "HOWIE\tRodney Thomas\tDeath notice\t09JUL2026\tDeath\t\t"
        "(born 07 Oct 1940 Adelaide)\tAdelaide Advertiser\t11JUL2026\n"
        "HOWIE\tRodney Thomas\tFuneral notice\t16JUL2026\tFuneral\t\t"
        "\tAdelaide Advertiser\t11JUL2026"
    )
    result=import_copied_ryerson_content(db,1,text)
    assert result["parsed"]==2
    assert result["stored"]==2
    findings=external_evidence_for_person(db,"@I1@")
    assert [f["evidence_type"] for f in findings]==["death_notice","funeral_notice"]
