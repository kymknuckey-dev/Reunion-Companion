from pathlib import Path
from reunion_companion.companion.database import connect
from reunion_companion.companion.gedcom import import_gedcom
from reunion_companion.companion.knowledge_graph import relationship_path,format_path,format_evidence_graph,format_topic_graph
from reunion_companion.companion.publishing_v7 import write_person_report,write_family_report
from reunion_companion.companion.guided import answer_question

GED="""0 HEAD
1 SOUR TEST
0 @S1@ SOUR
1 TEXT Birth Certificate.
0 @S2@ SOUR
1 TEXT Military archive.
0 @I1@ INDI
1 NAME Mervyn Neil /Knuckey/
1 SEX M
1 BIRT
2 DATE 24 SEP 1933
2 SOUR @S1@
1 FAMS @F1@
1 FAMC @F2@
0 @I2@ INDI
1 NAME Elaine Fay /Cox/
1 SEX F
1 FAMS @F1@
0 @I3@ INDI
1 NAME Kym Wayne /Knuckey/
1 SEX M
1 BIRT
2 DATE 17 JUL 1964
2 SOUR @S1@
1 FAMC @F1@
0 @I4@ INDI
1 NAME Victor Alexander /Knuckey/
1 SEX M
1 FAMS @F2@
0 @I5@ INDI
1 NAME Lois Aletha /Waight/
1 SEX F
1 FAMS @F2@
1 FAMC @F3@
0 @I6@ INDI
1 NAME Lionel George /Waight/
1 SEX M
1 FAMC @F3@
1 _MILS @N1@
0 @I7@ INDI
1 NAME Albert William /Waight/
1 SEX M
1 FAMS @F3@
0 @I8@ INDI
1 NAME Eva Alice /Manners/
1 SEX F
1 FAMS @F3@
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
1 MARR
2 DATE 21 JAN 1961
0 @F2@ FAM
1 HUSB @I4@
1 WIFE @I5@
1 CHIL @I1@
0 @F3@ FAM
1 HUSB @I7@
1 WIFE @I8@
1 CHIL @I5@
1 CHIL @I6@
0 @N1@ NOTE
1 CONT Lionel served in Borneo.
2 SOUR @S2@
0 TRLR
"""

def db(tmp_path):
    p=tmp_path/'x.ged';p.write_text(GED);d=connect(tmp_path/'x.sqlite3');import_gedcom(d,p);return d

def test_relationship_path(tmp_path):
    d=db(tmp_path);p=relationship_path(d,1,6)
    assert p is not None and len(p)==2
    out=format_path(d,1,6)
    assert 'Lois Aletha Waight' in out and 'Lionel George Waight' in out

def test_ask_relationship_path(tmp_path):
    d=db(tmp_path);out=answer_question(d,'How is Mervyn Neil Knuckey related to Lionel George Waight?')
    assert 'Intent: relationship path' in out
    assert 'Relationship Path' in out

def test_evidence_graph(tmp_path):
    d=db(tmp_path);out=format_evidence_graph(d,6)
    assert 'Knowledge Graph — Lionel George Waight' in out
    assert 'Military Service' in out
    assert 'Military archive.' in out

def test_topic_graph(tmp_path):
    d=db(tmp_path);out=format_topic_graph(d,'Borneo')
    assert 'Lionel George Waight' in out
    assert 'note' in out

def test_person_publish_html(tmp_path):
    d=db(tmp_path);p=write_person_report(d,6,tmp_path/'lionel.html')
    t=p.read_text()
    assert '<h1>Lionel George Waight</h1>' in t
    assert 'Lionel served in Borneo.' in t
    assert 'Military archive.' in t

def test_family_publish_html(tmp_path):
    d=db(tmp_path);p=write_family_report(d,1,tmp_path/'fam.html');t=p.read_text()
    assert 'Family of Mervyn Neil Knuckey' in t
    assert 'Elaine Fay Cox' in t and 'Kym Wayne Knuckey' in t
