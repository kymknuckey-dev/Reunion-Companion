from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import person_page
from reunion_companion.companion.ryerson_browser_assist import import_copied_ryerson_content
from reunion_companion.companion.external_evidence import external_evidence_for_person


def person(db,pid,xref,given,surname,display=None):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,xref,pid,given,surname,display or f"{given} {surname}","M",f"{given} /{surname}/"),
    )


def event(db,pid,kind,date=None,place=None,note=None):
    return db.execute(
        "INSERT INTO events(person_id,event_type,date_text,place_text,note_text) VALUES(?,?,?,?,?)",
        (pid,kind,date,place,note),
    ).lastrowid


def test_person_research_removes_obsolete_manual_ryerson_entry_ui(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Peter Stanley","Rigg")
    event(db,1,"Birth","21 May 1944","Brighton Community Hospital")
    db.commit()

    html=person_page(db,1,"research",presentation_override=False)

    assert "External Evidence" in html
    assert "Search Ryerson" not in html
    assert "Paste Ryerson result" not in html
    assert "Import and assess finding" not in html
    assert "/research/ryerson/import/1" not in html


def test_manual_ryerson_import_machinery_remains_available_without_person_ui(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Peter Stanley","Rigg")
    event(db,1,"Birth","21 May 1944","Brighton Community Hospital")
    db.commit()

    copied=("RIGG\tPeter Stanley\tDeath notice\t02JAN2021\tDeath\t\tlate of Curramulka (born 21 May 1944)\tAdelaide Advertiser\t04JAN2021")
    result=import_copied_ryerson_content(db,1,copied)

    assert result["stored"]==1
    assert len(external_evidence_for_person(db,"@I1@"))==1
    html=person_page(db,1,"research",presentation_override=False)
    assert "Peter Stanley RIGG" in html
    assert "Adelaide Advertiser" in html


def test_evidence_anomaly_uses_overview_needs_evidence_badge_language(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Example","Person")
    event(db,1,"Birth","01 Jan 1900","Adelaide")
    db.commit()

    html=person_page(db,1,"research",presentation_override=False)

    assert "<span class='badge warn'>Needs evidence</span> Birth has no directly attached source or media evidence." in html
    assert "<span class='badge info'>evidence</span>" not in html
