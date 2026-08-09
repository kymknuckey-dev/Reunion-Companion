from reunion_companion.companion.database import connect
from reunion_companion.companion.timeline_engine import (
    parse_genealogy_date,source_number,timeline_for_person,event_detail,format_event_timeline_intelligence
)

def seed(db):
    db.execute("""INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name)
                  VALUES(1,'@I1@',1,'Test','Person','Test Person','M','Test /Person/')""")
    db.execute("""INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name)
                  VALUES(2,'@I2@',2,'Spouse','Person','Spouse Person','F','Spouse /Person/')""")
    db.execute("INSERT INTO families(id,gedcom_xref,marriage_date,marriage_place) VALUES(1,'@F1@','1 JUN 1930','Adelaide')")
    db.execute("INSERT INTO family_members VALUES(1,1,'Husband')")
    db.execute("INSERT INTO family_members VALUES(1,2,'Wife')")
    events=[
      (1,1,'Birth','1 JAN 1900','Adelaide','Y','Birth note','BIRT'),
      (2,1,'Education','1910','Mitcham','St Michaels','School note','EDUC'),
      (3,1,'Occupation','MAY 1920','Adelaide','Carpenter',None,'OCCU'),
      (4,1,'Marriage','1 JUN 1930','Adelaide',None,'Marriage note','MARR'),
      (5,1,'Residence','1950','Victor Harbor',None,None,'RESI'),
      (6,1,'Death','1 JAN 1980','Victor Harbor','Y',None,'DEAT'),
    ]
    db.executemany("INSERT INTO events VALUES(?,?,?,?,?,?,?,?)",events)
    db.execute("INSERT INTO sources(id,gedcom_xref,title,text,display_text) VALUES(7,'@S7@','Birth Certificate','Birth Certificate.','Birth Certificate.')")
    db.execute("INSERT INTO event_sources VALUES(1,7,'GEDCOM')")
    db.execute("INSERT INTO media(id,file_path,title,exists_on_disk) VALUES(1,'/tmp/birth.pdf','Birth Certificate',0)")
    db.execute("INSERT INTO event_media VALUES(1,1,'GEDCOM')")
    db.commit()

def test_date_precision_and_qualifiers():
    d=parse_genealogy_date("ABT 24 FEB 1912")
    assert (d.year,d.month,d.day,d.precision,d.qualifier)==(1912,2,24,"day","ABT")
    d=parse_genealogy_date("MAY 1976")
    assert (d.year,d.month,d.day,d.precision)==(1976,5,None,"month")
    d=parse_genealogy_date("1976")
    assert d.precision=="year"
    assert parse_genealogy_date("").precision=="unknown"

def test_source_number():
    assert source_number("@S7@")==7
    assert source_number("S91")==91
    assert source_number("Birth Certificate") is None

def test_timeline_orders_and_calculates(tmp_path):
    db=connect(tmp_path/"x.sqlite3");seed(db)
    t=timeline_for_person(db,1)
    assert [x["type"] for x in t["events"]]==["Birth","Education","Occupation","Marriage","Residence","Death"]
    assert t["events"][1]["age"]=="about 10 years"
    assert t["events"][3]["age"]=="30 years"
    assert t["events"][4]["since_previous"].startswith("20.")
    db.close()

def test_timeline_evidence_and_source_number(tmp_path):
    db=connect(tmp_path/"x.sqlite3");seed(db)
    e=timeline_for_person(db,1)["events"][0]
    assert e["evidence_status"]=="supported"
    assert e["source_count"]==1 and e["media_count"]==1
    assert e["sources"][0]["gedcom_xref"]=="@S7@"
    db.close()

def test_timeline_observations_are_advisory(tmp_path):
    db=connect(tmp_path/"x.sqlite3");seed(db)
    ev=timeline_for_person(db,1)["events"]
    education=next(x for x in ev if x["type"]=="Education")
    assert "No directly linked source" in education["observations"]
    assert "No directly linked media" in education["observations"]
    residence=next(x for x in ev if x["type"]=="Residence")
    assert any("Gap of about" in x for x in residence["observations"])
    db.close()

def test_related_people_for_marriage(tmp_path):
    db=connect(tmp_path/"x.sqlite3");seed(db)
    marriage=next(x for x in timeline_for_person(db,1)["events"] if x["type"]=="Marriage")
    assert marriage["related_people"][0]["display_name"]=="Spouse Person"
    db.close()

def test_event_detail_navigation(tmp_path):
    db=connect(tmp_path/"x.sqlite3");seed(db)
    d=event_detail(db,3)
    assert d["event"]["type"]=="Occupation"
    assert d["previous_event"]["type"]=="Education"
    assert d["next_event"]["type"]=="Marriage"
    db.close()

def test_format_uses_canonical_engine(tmp_path):
    db=connect(tmp_path/"x.sqlite3");seed(db)
    text=format_event_timeline_intelligence(db,1)
    assert "Timeline Intelligence — Test Person" in text
    assert "Source 7 — Birth Certificate." in text
    assert "Age:" in text
    db.close()
