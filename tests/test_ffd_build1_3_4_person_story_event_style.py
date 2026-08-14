from pathlib import Path
from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import render_get
from reunion_companion.companion.ffd_presentation import set_presentation_mode

def seed(db):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(1,'@I1@',1,'Mervyn','Knuckey','Mervyn Knuckey','M','Mervyn /Knuckey/')")
    db.execute("INSERT INTO events VALUES(1,1,'Birth','24 SEP 1933','Unley Private Hospital, Unley','Y','BD&M b: 305A-239.','BIRT')")
    db.commit()

def test_key_life_events_content_and_layout_retained(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db);set_presentation_mode(True)
    p=render_get(db,"/person/1",{})
    assert "Key Life Events" in p
    assert "ffd-milestone" in p
    assert "ffd-milestone-type" in p
    assert "ffd-milestone-title" in p
    assert "Birth" in p
    assert "24 SEP 1933" in p
    assert "Unley Private Hospital, Unley" in p
    assert "BD&amp;M b: 305A-239." in p
    assert "View event →" not in p
    db.close()

def test_style_override_matches_timeline_heading_hierarchy():
    from reunion_companion.companion import beta_ui
    src=Path(beta_ui.__file__).read_text()
    marker="FFD 1.3.4 — Person Story Event Style Alignment"
    assert marker in src
    block=src.split(marker,1)[1].split("*/",1)[1]
    assert ".ffd-milestone-type" in block
    assert "text-transform:none" in block
    assert "font-weight:700" in block
    assert ".ffd-milestone-title" in block
    assert ".ffd-milestone p" in block

def test_timeline_markup_not_reworked(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db);set_presentation_mode(True)
    p=render_get(db,"/person/1",{"tab":"timeline","view":"story"})
    assert "Life Timeline" in p
    assert "Research Timeline" not in p and "Data" not in p
    assert "View event →" not in p
    db.close()

def test_event_workspace_navigation_retained(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db);set_presentation_mode(True)
    p=render_get(db,"/event/1",{"view":"story"})
    assert "← Timeline" in p
    assert "/person/1?tab=timeline&view=story" in p
    db.close()
