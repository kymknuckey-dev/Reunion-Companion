from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import render_get
from reunion_companion.companion.ffd_presentation import set_presentation_mode

def seed(db):
    people=[
      (1,'@I1@',1,'Mervyn','Knuckey','Mervyn Knuckey','M','Mervyn /Knuckey/'),
      (2,'@I2@',2,'Elaine','Cox','Elaine Fay Cox','F','Elaine /Cox/'),
      (3,'@I3@',3,'Victor','Knuckey','Victor Alexander Knuckey','M','Victor /Knuckey/'),
      (4,'@I4@',4,'Lois','Waight','Lois Aletha Waight','F','Lois /Waight/'),
      (5,'@I5@',5,'Brian','Knuckey','Brian Victor Knuckey','M','Brian /Knuckey/'),
    ]
    db.executemany("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",people)
    db.execute("INSERT INTO families(id,gedcom_xref) VALUES(1,'@F1@')")
    db.execute("INSERT INTO families(id,gedcom_xref) VALUES(2,'@F2@')")
    for row in [(1,1,'Husband'),(1,2,'Wife'),(2,3,'Husband'),(2,4,'Wife'),(2,1,'Child'),(2,5,'Child')]:
        db.execute("INSERT INTO family_members VALUES(?,?,?)",row)
    db.execute("INSERT INTO events VALUES(1,1,'Birth','24 SEP 1933','Unley','Y','Birth note','BIRT')")
    db.commit()

def page(tmp_path,monkeypatch):
    monkeypatch.setenv("HOME",str(tmp_path))
    db=connect(tmp_path/"x.sqlite3");seed(db);set_presentation_mode(True)
    return db,render_get(db,"/person/1",{})

def test_person_story_uses_companion_style_links(tmp_path,monkeypatch):
    db,p=page(tmp_path,monkeypatch)
    assert "ffd-nav-pill" in p
    assert "ffd-action-card" in p
    assert "ffd-inline-link" in p
    assert "ffd-secondary-link" in p
    db.close()

def test_event_display_is_label_first_not_raw_link(tmp_path,monkeypatch):
    db,p=page(tmp_path,monkeypatch)
    assert "Life Story" in p
    assert "ffd-milestone-title" in p
    assert "View event →" not in p
    db.close()

def test_family_display_keeps_correct_relationships(tmp_path,monkeypatch):
    db,p=page(tmp_path,monkeypatch)
    assert "Father" in p and "Victor Alexander Knuckey" in p
    assert "Mother" in p and "Lois Aletha Waight" in p
    assert "Brother" in p and "Brian Victor Knuckey" in p
    assert "ffd-relation-arrow" in p
    db.close()

def test_section_language_aligned(tmp_path,monkeypatch):
    db,p=page(tmp_path,monkeypatch)
    assert "Life Story" in p
    assert "Life Story" in p
    assert "Immediate Family" in p
    assert "Close Family" in p
    # Sparse people omit Media & Documents until image previews are available.
    assert "Explore Further" not in p
    db.close()
