from reunion_companion.companion.database import connect
from reunion_companion.companion.gedcom import import_gedcom
from reunion_companion.companion.guided import (
    answer_question,format_case,format_topic,format_military,format_documents,
    person_candidates_from_question
)

GED="""0 HEAD
1 SOUR TEST
0 @S5@ SOUR
1 TEXT Research by Mervyn Neil Knuckey .
0 @S7@ SOUR
1 TEXT Birth Certificate.
0 @S91@ SOUR
1 TYPE Commonwealth Dpt. of Veteran's Affairs.
1 TEXT Commonwealth Department of Veteran's Affairs.
0 @I1@ INDI
1 NAME Mervyn Neil /Knuckey/
1 SEX M
1 BIRT
2 DATE 24 SEP 1933
2 PLAC Unley Private Hospital, Unley, South Australia.
2 SOUR @S7@
1 _MILS @N1@
1 FAMS @F1@
0 @I2@ INDI
1 NAME Lionel George /Waight/
1 SEX M
1 BIRT
2 DATE 24 FEB 1912
2 PLAC Adelaide, South Australia.
1 NOTE @N2@
1 HIST @N3@
1 _MILS @N4@
1 FAMS @F1@
0 @I3@ INDI
1 NAME Test Child /Waight/
1 SEX M
1 FAMC @F1@
0 @F1@ FAM
1 HUSB @I2@
1 WIFE @I1@
1 CHIL @I3@
0 @N1@ NOTE
1 CONT Air Force service commenced in 1952. Mervyn Knuckey was known as ACR Knuckey A41392.
2 SOUR @S91@
0 @N2@ NOTE
1 CONT It is believed that Lionel was born Lionel George Anderson and was adopted by Albert and Eva as a son from birth.
2 SOUR @S5@
0 @N3@ NOTE
1 CONT Lionel later lived at Victor Harbor.
0 @N4@ NOTE
1 CONT Lionel served in the Australian Army in Borneo, including Balakpappan.
2 SOUR @S91@
0 TRLR
"""

def db(tmp_path):
    g=tmp_path/"tree.ged";g.write_text(GED)
    d=connect(tmp_path/"x.sqlite3");import_gedcom(d,g);return d

def test_person_mention_and_overview(tmp_path):
    d=db(tmp_path)
    ids=person_candidates_from_question(d,"What do we know about Lionel George Waight?")
    assert ids and ids[0]==2
    out=answer_question(d,"What do we know about Lionel George Waight?")
    assert "Intent: person overview" in out
    assert "Lionel George Waight" in out
    assert "[Military Service]" in out

def test_evidence_why_question(tmp_path):
    d=db(tmp_path)
    out=answer_question(d,"Why do we think Lionel George Waight was adopted?")
    assert "Intent: evidence question" in out
    assert "adopted" in out.lower()
    assert "@S5@" in out
    assert "does not by itself prove" in out

def test_topic_and_military_questions(tmp_path):
    d=db(tmp_path)
    out=answer_question(d,"Who served in Borneo?")
    assert "Intent: military-service discovery" in out
    assert "Lionel George Waight" in out
    assert "Borneo" in out
    t=format_topic(d,"Victor Harbor")
    assert "Lionel George Waight" in t
    m=format_military(d,"A41392")
    assert "Mervyn Neil Knuckey" in m

def test_case_and_relationship_question(tmp_path):
    d=db(tmp_path)
    c=format_case(d,2,"adopted")
    assert "Evidence Case" in c and "@S5@" in c
    q=answer_question(d,"Who are the children of Lionel George Waight?")
    assert "Intent: relationship question" in q
    assert "Test Child Waight" in q

def test_documents_safe_empty(tmp_path):
    d=db(tmp_path)
    out=format_documents(d,"Birth Certificate")
    assert "Document & Media Explorer" in out
