from reunion_companion.companion.database import connect
from reunion_companion.companion.gedcom import import_gedcom
from reunion_companion.companion.repair import format_notes,format_note_types,format_sources,format_evidence
from reunion_companion.companion.discovery_report import format_find
GED="""0 HEAD
1 SOUR TEST
0 @S91@ SOUR
1 TITL National Archives service record
0 @I1@ INDI
1 NAME Mervyn Neil /Knuckey/
1 SEX M
1 BIRT
2 DATE 24 SEP 1933
2 PLAC Unley Private Hospital
2 NOTE BD&M b: 305A-239.
2 SOUR @S91@
1 NOTE @N1@
1 HEAL @N2@
1 _MILS @N3@
0 @I2@ INDI
1 NAME Lionel George /Waight/
1 SEX M
1 _MILS @N194@
0 @N1@ NOTE
1 CONT After leaving School Mervyn's first job was with Bickfords.
1 CONT
1 CONT He later worked for the South Australian Health Commission.
0 @N2@ NOTE
1 CONT Mervyn was admitted to hospital in 1998.
0 @N3@ NOTE
1 CONT Mervyn Knuckey was known as ACR Knuckey A41392.
2 SOUR @S91@
0 @N194@ NOTE
1 CONT Waight, Lionel George, VX79391. Pte, Australian Army, serving at Bandjermasin & Balakpappan, Borneo.
2 SOUR @S91@
0 TRLR
"""
def test_repair(tmp_path):
    g=tmp_path/"x.ged";g.write_text(GED)
    db=connect(tmp_path/"x.sqlite3");c=import_gedcom(db,g)
    assert c["notes"]==4
    assert c["event_sources"]==1
    assert c["note_sources"]==2
    m=format_notes(db,1)
    assert "After leaving School" in m and "A41392" in m and "admitted to hospital" in m
    inv=format_note_types(db)
    assert "Medical" in inv and "Military Service" in inv
    assert "A41392" in format_find(db,"A41392")
    assert "Balakpappan" in format_find(db,"Balakpappan")
    assert "National Archives service record" in format_sources(db,2)
    ev=format_evidence(db,1)
    assert "Event source links: 1" in ev and "Note source links: 1" in ev
