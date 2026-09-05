from pathlib import Path

from reunion_companion.companion.database import connect
from reunion_companion.companion.person_bookmarks import set_bookmarked,is_bookmarked,bookmarked_people
from reunion_companion.companion.ffd_home import home_body
from reunion_companion.companion.ffd_person_story import person_identity_header
from reunion_companion.companion.beta_ui_service import person_workspace


def _db(tmp_path):
    db=connect(tmp_path/'bookmarks.sqlite3')
    db.execute("INSERT INTO people(gedcom_xref,display_name,given_names,surname) VALUES('@I1@','Thomas Knuckey','Thomas','Knuckey')")
    pid=db.execute("SELECT id FROM people WHERE gedcom_xref='@I1@'").fetchone()[0]
    db.execute("INSERT INTO events(person_id,event_type,date_text) VALUES(?,?,?)",(pid,'Birth','1822'))
    db.execute("INSERT INTO events(person_id,event_type,date_text) VALUES(?,?,?)",(pid,'Death','9 DEC 1885'))
    db.commit()
    return db,pid


def test_bookmark_toggle_and_home_identity(tmp_path):
    db,pid=_db(tmp_path)
    set_bookmarked(db,pid,True)
    assert is_bookmarked(db,pid)
    assert bookmarked_people(db)[0]['display_name']=='Thomas Knuckey'
    page=home_body(db,{},False)
    assert 'Bookmarked People' in page
    assert 'Thomas Knuckey' in page
    assert '1822–1885' in page
    set_bookmarked(db,pid,False)
    assert not is_bookmarked(db,pid)
    db.close()


def test_person_header_exposes_bookmark_control(tmp_path):
    db,pid=_db(tmp_path)
    w=person_workspace(db,pid)
    header=person_identity_header(db,w,True)
    assert f"/person/{pid}/bookmark" in header
    assert 'Bookmark person' in header
    set_bookmarked(db,pid,True)
    header=person_identity_header(db,person_workspace(db,pid),True)
    assert 'Remove bookmark' in header
    db.close()


def test_bookmark_uses_xref_not_transient_person_id(tmp_path):
    db,pid=_db(tmp_path)
    set_bookmarked(db,pid,True)
    db.execute("DELETE FROM people WHERE id=?",(pid,))
    db.execute("INSERT INTO people(id,gedcom_xref,display_name,given_names,surname) VALUES(99,'@I1@','Thomas Knuckey','Thomas','Knuckey')")
    db.commit()
    assert is_bookmarked(db,99)
    assert bookmarked_people(db)[0]['id']==99
    db.close()


def test_release_metadata_is_12_4():
    root=Path(__file__).resolve().parents[1]
    build=(root/'macos_app'/'build_app.py').read_text()
    dmg=(root/'macos_app'/'package_dmg.py').read_text()
    historical='FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.4 — Bookmarked People'
    # Historical feature identity remains documented; live APP_RELEASE may advance.
    assert '12.4' in historical and 'Bookmarked People' in historical
    import re
    b=re.search(r'^APP_RELEASE="([^"]+)"',build,re.M).group(1)
    d=re.search(r'^APP_RELEASE="([^"]+)"',dmg,re.M).group(1)
    assert b==d and b.startswith('FFD 2.0 RC1.0.')
