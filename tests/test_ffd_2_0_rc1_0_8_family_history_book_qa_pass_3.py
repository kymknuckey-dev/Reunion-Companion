from pathlib import Path

from reunion_companion.companion.database import connect
from reunion_companion.companion.family_publication_model import family_publication_media


def _seed_family(db):
    db.execute("INSERT INTO people(id,display_name) VALUES(1,'Husband Example')")
    db.execute("INSERT INTO people(id,display_name) VALUES(2,'Wife Example')")
    db.execute("INSERT INTO families(id) VALUES(10)")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(10,1,'Husband')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(10,2,'Wife')")


def test_generic_certificate_attached_only_to_family_is_marriage_document(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    _seed_family(db)
    cert=tmp_path/'certificate.jpg'; cert.write_bytes(b'x')
    cur=db.execute("INSERT INTO media(file_path,title,media_type,exists_on_disk,attachment_scope,attachment_label) VALUES(?,?,?,?,?,?)",
                   (str(cert),'Certificate','image/jpeg',1,'family','Certificate'))
    mid=cur.lastrowid
    db.execute("INSERT INTO family_media(family_id,media_id,relation) VALUES(10,?,'GEDCOM')",(mid,))
    family,wedding,docs=family_publication_media(db,10,1,2)
    assert [m['id'] for m in docs]==[mid]
    assert [m['id'] for m in family]==[mid]
    db.close()


def test_family_marriage_document_is_deduplicated_if_also_person_linked(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    _seed_family(db)
    cert=tmp_path/'certificate.pdf'; cert.write_bytes(b'%PDF')
    cur=db.execute("INSERT INTO media(file_path,title,media_type,exists_on_disk,attachment_scope,attachment_label) VALUES(?,?,?,?,?,?)",
                   (str(cert),'Certificate','application/pdf',1,'family','Certificate'))
    mid=cur.lastrowid
    db.execute("INSERT INTO family_media(family_id,media_id,relation) VALUES(10,?,'GEDCOM')",(mid,))
    db.execute("INSERT INTO person_media(person_id,media_id,relation) VALUES(1,?,'GEDCOM')",(mid,))
    _,_,docs=family_publication_media(db,10,1,2)
    assert [m['id'] for m in docs]==[mid]
    db.close()
