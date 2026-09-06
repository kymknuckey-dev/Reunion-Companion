from pathlib import Path

from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui_service import person_workspace
from reunion_companion.companion.ffd_person_story import person_identity_header
from reunion_companion.companion.family_publication_model import person_document_groups


def _person(db):
    return db.execute("INSERT INTO people(gedcom_xref,display_name,sex) VALUES('@I258@','Thomas Knuckey','M') RETURNING id").fetchone()[0]


def test_event_photo_is_not_promoted_to_person_header_portrait(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    pid=_person(db)
    photo=tmp_path/'Thomas & Johanna.jpg'; photo.write_bytes(b'jpg')
    eid=db.execute("INSERT INTO events(person_id,event_type,date_text) VALUES(?,?,?)",(pid,'Burial','10 DEC 1885')).lastrowid
    mid=db.execute("INSERT INTO media(file_path,title,media_type,exists_on_disk,attachment_scope,attachment_label,is_preferred) VALUES(?,?,?,?,?,?,?)",(str(photo),'Thomas & Johanna','PHOTO',1,'event','Burial',0)).lastrowid
    db.execute("INSERT INTO event_media(event_id,media_id,relation) VALUES(?,?,'GEDCOM')",(eid,mid))
    html=person_identity_header(db,person_workspace(db,pid),True)
    assert f"/media-file/{mid}" not in html
    db.close()


def test_publication_portrait_requires_direct_person_media(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    pid=_person(db)
    event_photo=tmp_path/'event.jpg'; event_photo.write_bytes(b'jpg')
    eid=db.execute("INSERT INTO events(person_id,event_type) VALUES(?,?)",(pid,'Residence')).lastrowid
    emid=db.execute("INSERT INTO media(file_path,title,media_type,exists_on_disk,attachment_scope,is_preferred) VALUES(?,?,?,?,?,?)",(str(event_photo),'At the farm','PHOTO',1,'event',0)).lastrowid
    db.execute("INSERT INTO event_media(event_id,media_id,relation) VALUES(?,?,'GEDCOM')",(eid,emid))
    assert person_document_groups(db,pid)['portrait']==[]

    person_photo=tmp_path/'person.jpg'; person_photo.write_bytes(b'jpg')
    pmid=db.execute("INSERT INTO media(file_path,title,media_type,exists_on_disk,attachment_scope,is_preferred) VALUES(?,?,?,?,?,?)",(str(person_photo),'Thomas portrait','PHOTO',1,'person',0)).lastrowid
    db.execute("INSERT INTO person_media(person_id,media_id,relation) VALUES(?,?,'GEDCOM')",(pid,pmid))
    groups=person_document_groups(db,pid)
    assert groups['portrait']==[]
    assert pmid in [m['id'] for m in groups['other-photos']]
    db.close()
