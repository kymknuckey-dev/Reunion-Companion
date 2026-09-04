from pathlib import Path

from reunion_companion.companion.database import connect
from reunion_companion.companion.publishing_v11 import book_html


def person(db,pid,name,sex='M'):
    db.execute('INSERT INTO people(id,display_name,sex) VALUES(?,?,?)',(pid,name,sex))


def family(db,fid,h,w,kids=()):
    db.execute('INSERT INTO families(id) VALUES(?)',(fid,))
    if h: db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Husband')",(fid,h))
    if w: db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Wife')",(fid,w))
    for kid in kids:
        db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Child')",(fid,kid))


def test_child_without_formed_family_is_published_as_terminal_individual(tmp_path, monkeypatch):
    db=connect(tmp_path/'child-only.sqlite3')
    person(db,1,'James Knuckey'); person(db,2,'Elizabeth Anne Hunter','F')
    person(db,3,'Charles Henry James Knuckey'); person(db,4,'Lyell Leonard Knuckey')
    person(db,5,'Louisa Maud Wenham','F')
    family(db,100,1,2,(3,4))
    family(db,101,3,5,())
    db.commit()

    # Keep the regression focused on scope/publication inclusion rather than
    # narrative generation.
    monkeypatch.setattr('reunion_companion.companion.publishing_v11._publication_biography',lambda db,pid:'')
    html=book_html(db,1,tmp_path/'book.html',4,end_pid=3,selected_family_ids=[100,101])

    assert 'Lyell Leonard Knuckey' in html
    assert "id='person-4'" in html
    assert html.count('Lyell Leonard Knuckey') >= 2  # life section + person index/chart context
    # Charles forms a family and therefore remains represented by that family
    # chapter rather than being emitted as a terminal child in his parents' chapter.
    assert html.count("id='person-3'") == 1
    db.close()


def test_release_identity_child_only_individual_inclusion():
    source=Path('macos_app/build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.9 — Child-only Individual Family-history Inclusion"' in source
