from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import render_get
from reunion_companion.companion.ffd_presentation import set_presentation_mode

def seed(db):
    people=[
      (1,'@I1@',1,'Mervyn Neil','Knuckey','Mervyn Neil Knuckey','M','Mervyn Neil /Knuckey/'),
      (2,'@I2@',2,'Elaine Fay','Cox','Elaine Fay Cox','F','Elaine Fay /Cox/'),
    ]
    db.executemany("""INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name)
                      VALUES(?,?,?,?,?,?,?,?)""",people)
    db.execute("INSERT INTO events VALUES(1,1,'Birth','24 SEP 1933','Unley','Y','Birth note','BIRT')")
    db.execute("INSERT INTO sources(id,gedcom_xref,title,text,display_text) VALUES(7,'@S7@','Birth Certificate',NULL,'Birth Certificate')")
    db.execute("INSERT INTO event_sources VALUES(1,7,'GEDCOM')")
    db.commit()

def test_sources_tab_uses_numbered_source_label(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    set_presentation_mode(True)
    p=render_get(db,"/person/1",{"tab":"sources"})
    assert "Source 7" in p
    assert "Birth Certificate" in p
    db.close()

def test_person_xref_hidden_in_presentation_header(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    set_presentation_mode(True)
    p=render_get(db,"/person/1",{"tab":"biography"})
    assert "Mervyn Neil Knuckey" in p
    assert "@I1@" not in p
    db.close()

def test_person_xref_retained_in_research_mode(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    set_presentation_mode(False)
    p=render_get(db,"/person/1",{"tab":"biography"})
    assert "@I1@" in p
    db.close()

def test_family_to_explore_hides_xref_in_presentation(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    set_presentation_mode(True)
    p=render_get(db,"/",{})
    assert "Family to Explore" in p
    assert "Mervyn Neil Knuckey" in p
    assert "@I1@" not in p
    db.close()

def test_family_to_explore_retains_xref_in_research_mode(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    set_presentation_mode(False)
    p=render_get(db,"/",{})
    assert "Mervyn Neil Knuckey" in p
    assert "@I1@" in p
    db.close()

def test_timeline_and_event_navigation_retained(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db)
    set_presentation_mode(True)
    timeline=render_get(db,"/person/1",{"tab":"timeline","view":"story"})
    assert "View event →" in timeline
    event=render_get(db,"/event/1",{"view":"story"})
    assert "← Timeline" in event
    db.close()
