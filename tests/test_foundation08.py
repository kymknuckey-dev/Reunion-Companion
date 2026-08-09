from pathlib import Path
from reunion_companion.companion.database import connect
from reunion_companion.companion.gedcom import import_gedcom
from reunion_companion.companion.relationship_engine import interpret_relationship,format_relationship
from reunion_companion.companion.story_engine import format_story
from reunion_companion.companion.research_engine import format_improve
from reunion_companion.companion.evidence_engine import format_evidence_intelligence,overall_evidence_score
from reunion_companion.companion.timeline_engine import format_timeline_intelligence
from reunion_companion.companion.knowledge_card import format_card
from reunion_companion.companion.audit_engine import format_audit
from reunion_companion.companion.publishing_v8 import write_biography
from reunion_companion.companion.guided import answer_question
from reunion_companion.companion.shell import CompanionShell

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
2 PLAC Unley, South Australia
2 SOUR @S1@
1 OCCU Electrical Supervisor
1 FAMC @F2@
0 @I2@ INDI
1 NAME Lois Aletha /Waight/
1 SEX F
1 FAMS @F2@
1 FAMC @F3@
0 @I3@ INDI
1 NAME Lionel George /Waight/
1 SEX M
1 FAMC @F3@
1 _MILS @N1@
0 @I4@ INDI
1 NAME Victor Alexander /Knuckey/
1 SEX M
1 FAMS @F2@
0 @I5@ INDI
1 NAME Albert William /Waight/
1 SEX M
1 FAMS @F3@
0 @I6@ INDI
1 NAME Eva Alice /Manners/
1 SEX F
1 FAMS @F3@
0 @I7@ INDI
1 NAME Child One /Knuckey/
1 SEX M
1 FAMC @F4@
1 FAMS @F6@
0 @I8@ INDI
1 NAME Sibling Parent /Knuckey/
1 SEX M
1 FAMC @F4@
1 FAMS @F5@
0 @I9@ INDI
1 NAME Cousin Child /Knuckey/
1 SEX F
1 FAMC @F5@
0 @I10@ INDI
1 NAME Common Father /Knuckey/
1 SEX M
1 FAMS @F4@
0 @I11@ INDI
1 NAME Common Mother /Smith/
1 SEX F
1 FAMS @F4@
0 @I12@ INDI
1 NAME Other Parent /Jones/
1 SEX F
1 FAMS @F5@
0 @F2@ FAM
1 HUSB @I4@
1 WIFE @I2@
1 CHIL @I1@
0 @F3@ FAM
1 HUSB @I5@
1 WIFE @I6@
1 CHIL @I2@
1 CHIL @I3@
0 @F4@ FAM
1 HUSB @I10@
1 WIFE @I11@
1 CHIL @I7@
1 CHIL @I8@
0 @F5@ FAM
1 HUSB @I8@
1 WIFE @I12@
1 CHIL @I9@
0 @I13@ INDI
1 NAME Cousin Peer /Knuckey/
1 SEX M
1 FAMC @F6@
0 @F6@ FAM
1 HUSB @I7@
1 CHIL @I13@
0 @N1@ NOTE
1 CONT Lionel served in Borneo.
2 SOUR @S2@
0 TRLR
"""

def make_db(tmp_path):
    p=tmp_path/"x.ged";p.write_text(GED)
    d=connect(tmp_path/"x.sqlite3");import_gedcom(d,p);return d

def test_maternal_uncle(tmp_path):
    d=make_db(tmp_path)
    rr=interpret_relationship(d,3,1)
    assert rr.label=="maternal uncle"
    out=format_relationship(d,3,1)
    assert "Maternal Uncle" in out
    assert "Lionel George Waight is brother of Lois Aletha Waight." in out
    assert "Lois Aletha Waight is mother of Mervyn Neil Knuckey." in out

def test_reverse_nephew(tmp_path):
    d=make_db(tmp_path)
    rr=interpret_relationship(d,1,3)
    assert rr.label=="nephew"

def test_first_cousin(tmp_path):
    d=make_db(tmp_path)
    rr=interpret_relationship(d,13,9)
    assert rr.label=="first cousin"

def test_ask_uses_relationship_intelligence(tmp_path):
    d=make_db(tmp_path)
    out=answer_question(d,"How is Lionel George Waight related to Mervyn Neil Knuckey?")
    assert "Intent: relationship intelligence" in out
    assert "Maternal Uncle" in out

def test_story_is_evidence_bound(tmp_path):
    d=make_db(tmp_path)
    out=format_story(d,3)
    assert "Lionel served in Borneo." in out
    assert "Provenance" in out

def test_timeline_chapters(tmp_path):
    d=make_db(tmp_path)
    out=format_timeline_intelligence(d,1)
    assert "Early Life" in out
    assert "Education & Working Life" in out

def test_evidence_intelligence(tmp_path):
    d=make_db(tmp_path)
    out=format_evidence_intelligence(d,1)
    assert "Birth Certificate." in out
    assert overall_evidence_score(d,1)>0

def test_research_assistant(tmp_path):
    d=make_db(tmp_path)
    out=format_improve(d,3)
    assert "Research Opportunities" in out

def test_knowledge_card(tmp_path):
    d=make_db(tmp_path)
    out=format_card(d,3)
    assert "Knowledge Card — Lionel George Waight" in out
    assert "Military            Yes" in out

def test_audit(tmp_path):
    d=make_db(tmp_path)
    out=format_audit(d,3)
    assert "Genealogy Audit — Lionel George Waight" in out
    assert "Audit scope" in out

def test_biography_output(tmp_path):
    d=make_db(tmp_path)
    p=write_biography(d,3,tmp_path/"bio.html")
    t=p.read_text()
    assert "Genealogical Intelligence Biography" in t
    assert "Lionel served in Borneo." in t
    assert "Military archive." in t

def test_workspace_open_and_current_commands(tmp_path):
    dpath=tmp_path/"shell.sqlite3"
    g=tmp_path/"g.ged";g.write_text(GED)
    d=connect(dpath);import_gedcom(d,g);d.close()
    sh=CompanionShell(dpath)
    out=sh.command('open "Lionel George Waight"')
    assert sh.current_person==3 and "Knowledge Card" in out
    assert "Life Story" in sh.command("story")
    rel=sh.command('relationship "Mervyn Neil Knuckey"')
    assert "Maternal Uncle" in rel
    assert "Workspace closed" in sh.command("close")
