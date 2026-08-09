from reunion_companion.companion.database import connect
from reunion_companion.companion.gedcom import import_gedcom
from reunion_companion.companion.repair import (
    format_sources, format_source, format_source_usage,
    format_citation_summary, format_evidence,
)
from reunion_companion.companion.discovery_report import format_find, format_tell

GED="""0 HEAD
1 SOUR TEST
0 @S4@ SOUR
1 TEXT St. Michaels Church of England Day School Mitcham.
0 @S5@ SOUR
1 TEXT Research by Mervyn Neil Knuckey .
0 @S7@ SOUR
1 TEXT Birth Certificate.
0 @S16@ SOUR
1 TEXT Crematorium Certificate.
0 @S17@ SOUR
1 TEXT South Australian Births, Deaths and Marriages Indices
0 @S91@ SOUR
1 TYPE Commonwealth Dpt. of Veteran’s Affairs.
1 TEXT Commonwealth Department of Veteran’s Affairs.
0 @I1@ INDI
1 NAME Mervyn Neil /Knuckey/
1 SEX M
1 BIRT
2 DATE 24 SEP 1933
2 SOUR @S7@
1 EDUC St. Michaels C/E. Mitcham
2 SOUR @S4@
1 NOTE @N1@
1 HEAL @N2@
1 _MILS @N3@
0 @I304@ INDI
1 NAME Lionel George /Waight/
1 SEX M
1 BIRT
2 DATE 24 FEB 1912
2 SOUR @S5@
1 BURI
2 DATE 10 JUN 1994
2 SOUR @S16@
1 NOTE @N192@
1 HIST @N193@
1 _MILS @N194@
0 @N1@ NOTE
1 CONT General Mervyn note.
0 @N2@ NOTE
1 CONT Medical Mervyn note.
0 @N3@ NOTE
1 CONT Mervyn Knuckey was known as ACR Knuckey A41392.
0 @N192@ NOTE
1 CONT It is believed that Lionel was born Lionel George Anderson.
2 SOUR @S17@
0 @N193@ NOTE
1 CONT Lionel research narrative.
0 @N194@ NOTE
1 CONT Waight, Lionel George, VX79391, serving at Bandjermasin & Balakpappan, Borneo.
2 SOUR @S91@
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I304@
1 MARR
2 DATE 1 JAN 1960
2 SOUR @S5@
0 TRLR
"""

def test_complete_source_model(tmp_path):
    g=tmp_path/'x.ged';g.write_text(GED)
    db=connect(tmp_path/'x.sqlite3')
    c=import_gedcom(db,g)
    assert c['sources']==6
    assert c['family_sources']==1
    assert c['event_sources']==4
    assert c['note_sources']==2
    assert c['citations']==7

    lionel=db.execute("SELECT id FROM people WHERE reunion_person_id=304").fetchone()[0]
    s=format_sources(db,lionel)
    assert '@S5@ [event] — Research by Mervyn Neil Knuckey .' in s
    assert '@S16@ [event] — Crematorium Certificate.' in s
    assert '@S17@ [note] — South Australian Births, Deaths and Marriages Indices' in s
    assert '@S91@ [note] — Commonwealth Department of Veteran’s Affairs.' in s
    assert 'Type: Commonwealth Dpt. of Veteran’s Affairs.' in s

    one=format_source(db,'91')
    assert 'Commonwealth Department of Veteran’s Affairs.' in one
    assert 'Note links: 1' in one
    usage=format_source_usage(db,'5')
    assert '304: Lionel George Waight' in usage
    assert '@F1@' in usage

    cs=format_citation_summary(db)
    assert 'Unique family-source links: 1' in cs
    assert 'Citation occurrences: 7' in cs

    assert 'A41392' in format_find(db,'A41392')
    assert 'Balakpappan' in format_find(db,'Balakpappan')
    tell=format_tell(db,lionel)
    assert '[Note]' in tell and '[Research]' in tell and '[Military Service]' in tell

    ev=format_evidence(db,lionel)
    assert 'Sources: 4' in ev
    assert 'Event source links: 2' in ev
    assert 'Note source links: 2' in ev
