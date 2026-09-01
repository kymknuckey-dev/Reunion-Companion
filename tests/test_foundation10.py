from pathlib import Path
import base64
from reunion_companion.companion.database import connect
from reunion_companion.companion.gedcom import import_gedcom
from reunion_companion.companion.family_publication_model import (
    family_overview,resolve_family_for_people,person_document_groups
)
from reunion_companion.companion.publishing_v10 import (
    preview_family,family_chapter_html,write_family_chapter,book_family_ids,write_book
)
from reunion_companion.companion.descendant_chart import chart_text
from reunion_companion.companion.shell import CompanionShell

# 1x1 valid PNG
PNG=base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl2n0kAAAAASUVORK5CYII=")

def make_ged(tmp):
    wedding=tmp/"Charles and Elizabeth Wedding.jpg";wedding.write_bytes(PNG)
    birth=tmp/"Charles 1879 Birth Certificate.jpg";birth.write_bytes(PNG)
    marriage_pdf=tmp/"Charles and Elizabeth Marriage Certificate.pdf";marriage_pdf.write_bytes(b"%PDF-1.4 test")
    return f"""0 HEAD
1 SOUR TEST
0 @S1@ SOUR
1 TEXT South Australian Birth Certificate.
0 @I1@ INDI
1 NAME Charles Henry James /Knuckey/
1 SEX M
1 BIRT
2 DATE 30 JAN 1879
2 PLAC Gilberton, South Australia
2 SOUR @S1@
2 OBJE
3 FILE {birth}
3 FORM image/jpeg
3 TITL Charles 1879 Birth Certificate
3 _TYPE PHOTO
1 NOTE @N1@
1 FAMS @F1@
1 FAMC @F2@
0 @I2@ INDI
1 NAME Elizabeth Anne /Hunter/
1 SEX F
1 BIRT
2 DATE 1 JAN 1880
1 FAMS @F1@
1 FAMC @F3@
0 @I3@ INDI
1 NAME Child One /Knuckey/
1 SEX M
1 BIRT
2 DATE 1903
1 FAMC @F1@
1 FAMS @F4@
0 @I4@ INDI
1 NAME Grandchild One /Knuckey/
1 SEX F
1 BIRT
2 DATE 1933
1 FAMC @F4@
0 @I5@ INDI
1 NAME Wife of Child /Jones/
1 SEX F
1 FAMS @F4@
0 @I6@ INDI
1 NAME Father Charles /Knuckey/
1 SEX M
1 FAMS @F2@
0 @I7@ INDI
1 NAME Mother Charles /Smith/
1 SEX F
1 FAMS @F2@
0 @I8@ INDI
1 NAME Father Elizabeth /Hunter/
1 SEX M
1 FAMS @F3@
0 @I9@ INDI
1 NAME Mother Elizabeth /Blakeley/
1 SEX F
1 FAMS @F3@
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
1 MARR
2 DATE 10 DEC 1902
2 PLAC Adelaide, South Australia
1 OBJE
2 FILE {marriage_pdf}
2 FORM application/pdf
2 TITL Charles and Elizabeth Marriage Certificate
2 _TYPE PDF
1 OBJE
2 FILE {wedding}
2 FORM image/jpeg
2 TITL Charles and Elizabeth Wedding
2 _TYPE PHOTO
0 @F2@ FAM
1 HUSB @I6@
1 WIFE @I7@
1 CHIL @I1@
0 @F3@ FAM
1 HUSB @I8@
1 WIFE @I9@
1 CHIL @I2@
0 @F4@ FAM
1 HUSB @I3@
1 WIFE @I5@
1 CHIL @I4@
0 @N1@ NOTE
1 CONT Charles worked as a coach body builder.
0 TRLR
"""

def db(tmp_path):
    p=tmp_path/"x.ged";p.write_text(make_ged(tmp_path))
    d=connect(tmp_path/"x.sqlite3");import_gedcom(d,p);return d

def test_family_overview_and_media(tmp_path):
    d=db(tmp_path);f=resolve_family_for_people(d,1,2);o=family_overview(d,f["id"])
    assert o["children_count"]==1
    assert len(o["wedding_photos"])==1
    assert len(o["marriage_documents"])==1

def test_preview_has_dad_order(tmp_path):
    d=db(tmp_path);o=preview_family(d,1)
    assert "Wedding photograph(s)" in o
    assert "Husband person page" in o
    assert "Wife person page" in o
    assert "descendant chart" in o

def test_person_birth_document_classified(tmp_path):
    d=db(tmp_path);g=person_document_groups(d,1)
    assert len(g["birth"])==1

def test_family_chapter_structure(tmp_path):
    d=db(tmp_path);t=family_chapter_html(d,1)
    order=[
        t.index("Family Overview"),
        t.index(">Marriage<"),
        t.index("<section class='person-summary'><h2>Charles Henry James Knuckey"),
        t.index("<section class='person-summary'><h2>Elizabeth Anne Hunter"),
        t.index("Family &amp; Descendants"),
    ]
    assert order==sorted(order)
    assert "<h2>Children</h2>" not in t
    assert "No children are recorded for this family." not in t
    assert "Sources Used in This Chapter" not in t
    assert "data:image/jpeg;base64," in t
    assert "Open PDF" in t

def test_chart_includes_both_parent_sides(tmp_path):
    d=db(tmp_path);t=chart_text(d,1,2,3)
    assert "Father Charles Knuckey" in t
    assert "Mother Charles Smith" in t
    assert "Father Elizabeth Hunter" in t
    assert "Mother Elizabeth Blakeley" in t
    assert "Grandchild One Knuckey" in t

def test_write_family_chapter(tmp_path):
    d=db(tmp_path);p=write_family_chapter(d,1,tmp_path/"chapter.html")
    assert p.exists() and "Dad Classic" not in p.read_text()  # theme acts through CSS rather than a label

def test_book_assembly(tmp_path):
    d=db(tmp_path);ids=book_family_ids(d,1,3)
    assert 1 in ids and 4 in ids
    p=write_book(d,1,tmp_path/"book.html",3)
    text=p.read_text()
    assert "Family History" in text
    assert "Chapter 1" in text

def test_shell_publishing_commands(tmp_path,monkeypatch):
    reports=tmp_path/"reports"
    monkeypatch.setenv("REUNION_COMPANION_REPORT_DIR",str(reports))
    ged=tmp_path/"x.ged";ged.write_text(make_ged(tmp_path))
    path=tmp_path/"shell.sqlite3";d=connect(path);import_gedcom(d,ged);d.close()
    sh=CompanionShell(path)
    assert "Dad Classic" in sh.command("publication-themes")
    assert "Publication theme set to" in sh.command('publication-theme "Clean Modern"')
    assert "Family Chapter Preview" in sh.command('preview-family "Charles Henry James Knuckey" "Elizabeth Anne Hunter"')
    assert "Family chapter written:" in sh.command('publish-family-chapter "Charles Henry James Knuckey" "Elizabeth Anne Hunter"')
    assert "Descendant chart written:" in sh.command('publish-descendant-chart "Charles Henry James Knuckey" "Elizabeth Anne Hunter" 3')
    assert "Family-history book written:" in sh.command('publish-book "Charles Henry James Knuckey" 3')
    produced=list(reports.glob("*.html"))
    assert len(produced)==3
    assert all(x.parent==reports for x in produced)
