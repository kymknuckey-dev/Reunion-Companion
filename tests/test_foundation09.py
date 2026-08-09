from reunion_companion.companion.database import connect
from reunion_companion.companion.gedcom import import_gedcom
from reunion_companion.companion.profile_builder import format_profile
from reunion_companion.companion.confidence_engine import format_confidence,overall_confidence
from reunion_companion.companion.gap_engine import format_research_gaps,research_gap_summary
from reunion_companion.companion.evidence_summary import format_evidence_summary
from reunion_companion.companion.media_health import format_media_health,media_health_data
from reunion_companion.companion.research_timeline import format_research_timeline
from reunion_companion.companion.publish_profile import write_profile
from reunion_companion.companion.shell import CompanionShell
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
2 PLAC Unley, South Australia
2 SOUR @S1@
1 OCCU Electrical Supervisor
1 NOTE @N1@
1 OBJE
2 FILE /definitely/missing/photo.pict
2 TITL Old portrait
2 _TYPE PHOTO
0 @I2@ INDI
1 NAME Lionel George /Waight/
1 SEX M
1 BIRT
2 DATE 24 FEB 1912
2 PLAC Adelaide, South Australia
1 _MILS @N2@
0 @I3@ INDI
1 NAME Sparse Person /Example/
1 SEX F
0 @N1@ NOTE
1 CONT In 1952 Mervyn completed National Service. In 1994 he retired.
0 @N2@ NOTE
1 CONT Lionel served in Borneo in 1945.
2 SOUR @S2@
0 TRLR
"""

def make_db(tmp_path):
    p=tmp_path/'x.ged';p.write_text(GED)
    d=connect(tmp_path/'x.sqlite3');import_gedcom(d,p);return d

def test_profile(tmp_path):
    d=make_db(tmp_path);o=format_profile(d,1)
    assert 'Research Profile — Mervyn Neil Knuckey' in o
    assert 'Research confidence' in o

def test_confidence(tmp_path):
    d=make_db(tmp_path);o=format_confidence(d,1)
    assert 'Birth' in o and 'linked source' in o
    assert overall_confidence(d,1)>0

def test_evidence_summary(tmp_path):
    d=make_db(tmp_path);o=format_evidence_summary(d,1)
    assert 'Birth Certificate.' in o
    assert 'Supported events' in o

def test_research_timeline_extracts_note_years(tmp_path):
    d=make_db(tmp_path);o=format_research_timeline(d,1)
    assert '1952' in o and '1994' in o and '[NOTE]' in o

def test_gap_dashboard(tmp_path):
    d=make_db(tmp_path);x=research_gap_summary(d);o=format_research_gaps(d)
    assert x['missing_birth']>=1
    assert 'Sparse Person Example' in o

def test_media_health_missing(tmp_path):
    d=make_db(tmp_path);x=media_health_data(d);o=format_media_health(d)
    assert len(x['missing'])==1
    assert 'Missing Media' in o and 'Old portrait' in o

def test_publish_profile(tmp_path):
    d=make_db(tmp_path);p=write_profile(d,1,tmp_path/'profile.html');t=p.read_text()
    assert 'Foundation 09 Research Intelligence Profile' in t
    assert 'Integrated Timeline' in t
    assert 'Birth Certificate.' in t

def test_workspace_f9_commands(tmp_path):
    g=tmp_path/'x.ged';g.write_text(GED);path=tmp_path/'shell.sqlite3';d=connect(path);import_gedcom(d,g);d.close();sh=CompanionShell(path)
    sh.command('open "Mervyn Neil Knuckey"')
    assert 'Research Profile' in sh.command('profile')
    assert 'Research Confidence' in sh.command('confidence')
    assert 'Evidence Summary' in sh.command('evidence-summary')
    assert 'Integrated Research Timeline' in sh.command('research-timeline')

def test_guided_profile_intent(tmp_path):
    d=make_db(tmp_path);o=answer_question(d,'What is the research profile for Mervyn Neil Knuckey?')
    assert 'Intent: research profile' in o
