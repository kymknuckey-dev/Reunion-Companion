from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence import external_evidence_for_person
from reunion_companion.companion.ryerson_harvest import (
    cache_harvest_rows,
    cached_notices,
    cross_match_cached_notices,
    harvest_record_key,
)

def person(db,pid,xref,given,surname,display=None):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,xref,pid,given,surname,display or f"{given} {surname}","M",f"{given} /{surname}/"),
    )

def event(db,pid,kind,date=None,place=None,note=None):
    db.execute(
        "INSERT INTO events(person_id,event_type,date_text,place_text,note_text) VALUES(?,?,?,?,?)",
        (pid,kind,date,place,note),
    )

PETER={
    "evidence_type":"death_notice",
    "source_record_name":"Peter Stanley RIGG",
    "event_type":"Death",
    "event_date":"02JAN2021",
    "publication":"Adelaide Advertiser",
    "publication_date":"04JAN2021",
    "details":"late of Curramulka (born 21 May 1944)",
    "birth_date_claim":"21 May 1944",
    "place_claim":"Curramulka",
}

RODNEY={
    "evidence_type":"death_notice",
    "source_record_name":"Rodney Thomas HOWIE",
    "event_type":"Death",
    "event_date":"09JUL2026",
    "publication":"Adelaide Advertiser",
    "publication_date":"11JUL2026",
    "details":"born 07 Oct 1940 Adelaide",
    "birth_date_claim":"07 Oct 1940",
    "place_claim":None,
}

def test_notice_key_is_stable():
    assert harvest_record_key(PETER)==harvest_record_key(dict(PETER))

def test_repeated_harvest_is_deduplicated(tmp_path):
    db=connect(tmp_path/"x.db")
    first=cache_harvest_rows(db,[PETER],harvest_kind="location",harvest_value="Adelaide",harvest_year=2021,page_number=1)
    second=cache_harvest_rows(db,[PETER],harvest_kind="location",harvest_value="Adelaide",harvest_year=2021,page_number=2)
    assert first["inserted"]==1
    assert second["inserted"]==0
    assert second["existing"]==1
    assert len(cached_notices(db,year=2021))==1

def test_peter_rigg_known_positive_matches_locally(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Peter Stanly","Rigg","Peter Stanly Rigg")
    event(db,1,"Birth","21 May 1944","Brighton Community Hospital")
    db.commit()
    cache_harvest_rows(db,[PETER],harvest_kind="location",harvest_value="Adelaide",harvest_year=2021)
    result=cross_match_cached_notices(db,year=2021)
    assert result["created_findings"]==1
    finding=external_evidence_for_person(db,"@I1@")[0]
    assert finding["event_date"]=="02JAN2021"
    assert finding["match_confidence"]>=80

def test_rodney_howie_known_positive_matches_locally(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Rodney Thomas","Howie","Rodney Thomas Howie")
    event(db,1,"Birth","07 Oct 1940","Adelaide, South Australia")
    db.commit()
    cache_harvest_rows(db,[RODNEY],harvest_kind="location",harvest_value="Adelaide",harvest_year=2026)
    result=cross_match_cached_notices(db,year=2026)
    assert result["created_findings"]==1
    finding=external_evidence_for_person(db,"@I1@")[0]
    assert finding["event_date"]=="09JUL2026"
    assert finding["match_confidence"]>=80

def test_existing_recorded_death_is_not_researched(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Rodney Thomas","Howie","Rodney Thomas Howie")
    event(db,1,"Birth","07 Oct 1940","Adelaide, South Australia")
    death=db.execute("INSERT INTO events(person_id,event_type,date_text,place_text) VALUES(1,'Death','09 JUL 2026','Adelaide')").lastrowid
    db.execute("INSERT INTO sources(id,gedcom_xref,title) VALUES(1,'@S1@','Death source')")
    db.execute("INSERT INTO event_sources(event_id,source_id,relation) VALUES(?,1,'GEDCOM')",(death,))
    db.commit()
    cache_harvest_rows(db,[RODNEY],harvest_kind="location",harvest_value="Adelaide",harvest_year=2026)
    result=cross_match_cached_notices(db,year=2026)
    assert result["created_findings"]==0
    assert external_evidence_for_person(db,"@I1@")==[]

def test_cross_match_is_idempotent(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Peter Stanly","Rigg","Peter Stanly Rigg")
    event(db,1,"Birth","21 May 1944","Brighton Community Hospital")
    db.commit()
    cache_harvest_rows(db,[PETER],harvest_kind="location",harvest_value="Adelaide",harvest_year=2021)
    first=cross_match_cached_notices(db,year=2021)
    second=cross_match_cached_notices(db,year=2021)
    assert first["created_findings"]==1
    assert second["created_findings"]==0
    assert len(external_evidence_for_person(db,"@I1@"))==1
