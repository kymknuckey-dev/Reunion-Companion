from reunion_companion.companion.database import connect
from reunion_companion.companion.gedcom import import_gedcom
from reunion_companion.companion.guided import answer_question
from reunion_companion.companion.entities import resolve_entities
from reunion_companion.companion.intelligence import records_for_person,format_assess,format_conflicts

GED="""0 HEAD
1 SOUR TEST
0 @S5@ SOUR
1 TEXT Research by Mervyn Neil Knuckey .
0 @S7@ SOUR
1 TEXT Birth Certificate.
0 @S91@ SOUR
1 TEXT Commonwealth Department of Veteran's Affairs.
0 @I1@ INDI
1 NAME Kym Wayne /Knuckey/
1 SEX M
1 BIRT
2 DATE 17 JUL 1964
2 SOUR @S7@
1 OCCU Drafter
1 FAMS @F1@
0 @I2@ INDI
1 NAME Lionel George /Waight/
1 SEX M
1 BIRT
2 DATE 24 FEB 1912
1 NOTE @N2@
1 _MILS @N4@
0 @I3@ INDI
1 NAME Test Child /Knuckey/
1 FAMC @F1@
0 @F1@ FAM
1 HUSB @I1@
1 CHIL @I3@
0 @N2@ NOTE
1 CONT It is believed Lionel was adopted.
2 SOUR @S5@
0 @N4@ NOTE
1 CONT Lionel served in Borneo at Balakpappan.
2 SOUR @S91@
0 TRLR
"""

def make_db(tmp_path):
    g=tmp_path/"tree.ged";g.write_text(GED)
    d=connect(tmp_path/"x.sqlite3");import_gedcom(d,g);return d

def test_entity_first_records_question(tmp_path):
    d=make_db(tmp_path)
    ents=resolve_entities(d,"what records mention kym wayne Knuckey")
    assert ents and ents[0].kind=="person" and ents[0].object_id==1
    out=answer_question(d,"what records mention kym wayne Knuckey")
    assert "Intent: person-connected records" in out
    assert "Records Connected to — Kym Wayne Knuckey" in out
    assert "Birth — 17 JUL 1964" in out
    assert "@S7@" in out

def test_identifier_is_not_forced_into_person(tmp_path):
    d=make_db(tmp_path)
    out=answer_question(d,"find Balakpappan")
    assert "Topic Explorer" in out or "identifier" in out.lower()

def test_research_intelligence(tmp_path):
    d=make_db(tmp_path)
    out=format_assess(d,1)
    assert "Research Intelligence — Kym Wayne Knuckey" in out
    assert "Birth" in out and "source" in out.lower()
    assert "Occupation" not in out.split("Potentially unsupported event assertions")[1].split("Conflicts")[0]

def test_conflict_detection(tmp_path):
    d=make_db(tmp_path)
    d.execute("INSERT INTO events(person_id,event_type,date_text,gedcom_tag) VALUES(1,'Birth','18 JUL 1964','BIRT')")
    d.commit()
    out=format_conflicts(d,1)
    assert "17 JUL 1964" in out and "18 JUL 1964" in out

def test_records_structural_not_literal_name_search(tmp_path):
    d=make_db(tmp_path)
    out=records_for_person(d,1)
    assert "Kym Wayne Knuckey" in out
    assert "Drafter" in out
    assert "Birth Certificate." in out
