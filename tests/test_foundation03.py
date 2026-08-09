from reunion_companion.companion.database import connect
from reunion_companion.companion.gedcom import import_gedcom
from reunion_companion.companion.discovery import cross_search,relationship_connections,descendants,research_gaps
GED="""0 HEAD
0 @I1@ INDI
1 NAME Test /Probe/
1 BIRT
2 DATE 2 JAN 1926
2 PLAC Adelaide
1 NOTE Overland Telegraph research
0 @I2@ INDI
1 NAME Mary /Probe/
0 @I3@ INDI
1 NAME Baby /Probe/
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
0 TRLR
"""
def test_f3(tmp_path):
 g=tmp_path/'p.ged';g.write_text(GED);db=connect(tmp_path/'d.sqlite3');import_gedcom(db,g);assert cross_search(db,'Overland Telegraph');assert relationship_connections(db,1)['children'][0]['display_name']=='Baby Probe';assert descendants(db,1)[0][1]['display_name']=='Baby Probe';assert any(x[0]=='Death' for x in research_gaps(db,1))
