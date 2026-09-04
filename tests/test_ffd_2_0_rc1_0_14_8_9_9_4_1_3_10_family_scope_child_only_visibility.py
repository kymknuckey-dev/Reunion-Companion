from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import book_scope_page


def person(db,pid,name,sex="M"):
    db.execute("INSERT INTO people(id,display_name,sex) VALUES(?,?,?)",(pid,name,sex))


def family(db,fid,h,w,kids=()):
    db.execute("INSERT INTO families(id) VALUES(?)",(fid,))
    if h: db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Husband')",(fid,h))
    if w: db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Wife')",(fid,w))
    for kid in kids: db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Child')",(fid,kid))


def test_child_without_family_is_visible_as_terminal_individual_in_scope_selector(tmp_path):
    db=connect(tmp_path/'scope.sqlite3')
    person(db,1,'James Knuckey'); person(db,2,'Elizabeth Anne Hunter','F')
    person(db,3,'Charles Henry James Knuckey'); person(db,4,'Lyell Leonard Knuckey')
    person(db,5,'Louisa Maud Wenham','F')
    family(db,100,1,2,(3,4)); family(db,101,3,5,())
    db.commit()
    html=book_scope_page(db,1,{'endpoint':'3'})
    assert 'Lyell Leonard Knuckey' in html
    assert 'Individual — no family branch' in html
    assert "name='family_101'" in html
    assert "name='family_4'" not in html
    assert "name='individual_4'" in html
    db.close()
