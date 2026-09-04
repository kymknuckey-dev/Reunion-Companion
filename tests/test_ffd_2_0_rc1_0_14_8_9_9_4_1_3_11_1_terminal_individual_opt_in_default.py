from pathlib import Path

from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import book_scope_page


def person(db,pid,name,sex="M"):
    db.execute("INSERT INTO people(id,display_name,sex) VALUES(?,?,?)",(pid,name,sex))

def family(db,fid,h,w,kids=()):
    db.execute("INSERT INTO families(id) VALUES(?)",(fid,))
    if h: db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Husband')",(fid,h))
    if w: db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Wife')",(fid,w))
    for kid in kids: db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Child')",(fid,kid))

def test_terminal_individuals_are_opt_in_by_default(tmp_path):
    db=connect(tmp_path/'scope.sqlite3')
    person(db,1,'James Knuckey'); person(db,2,'Elizabeth Anne Hunter','F')
    person(db,3,'Charles Henry James Knuckey'); person(db,4,'Lyell Leonard Knuckey')
    person(db,5,'Louisa Maud Wenham','F')
    family(db,100,1,2,(3,4)); family(db,101,3,5,())
    db.commit()
    html=book_scope_page(db,1,{'endpoint':'3'})
    assert "name='individual_4' value='1'" in html
    assert "name='individual_4' value='1' checked" not in html
    assert 'Individual — no family branch' in html
    db.close()

def test_release_identity_terminal_individual_opt_in_default():
    source=Path('macos_app/build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.11.1 — Terminal Individual Opt-in Default"' in source
