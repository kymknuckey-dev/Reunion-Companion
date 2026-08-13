from pathlib import Path
import pytest
from reunion_companion.companion.database import connect
from reunion_companion.companion.family_files import (
    active_family_file, register_family_file, rename_family_file, set_default_family,
    delete_family_file, list_family_files, family_report_count, ensure_family_files,
)
from reunion_companion.companion.beta3_publishing import _record, publication_history
from reunion_companion.companion.beta_ui import render_get


def ged(path,name='Alpha Person'):
    first,last=name.split()[0],name.split()[-1]
    path.write_text(f"0 HEAD\n1 SOUR Reunion\n0 @I1@ INDI\n1 NAME {first} /{last}/\n1 SEX M\n1 BIRT\n2 DATE 1 JAN 1900\n0 TRLR\n")
    return path


def test_family_file_can_be_renamed_without_identity_change(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); g=ged(tmp_path/'a.ged')
    wid=register_family_file(db,'Hewitt Family 14',g,'Reunion')
    before=next(x for x in list_family_files(db) if x['id']==wid)
    rename_family_file(db,wid,'Hewitt Family History')
    after=next(x for x in list_family_files(db) if x['id']==wid)
    assert after['display_name']=='Hewitt Family History'
    assert after['workspace_uuid']==before['workspace_uuid']


def test_default_and_active_family_cannot_be_deleted(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); g=ged(tmp_path/'a.ged')
    wid=register_family_file(db,'Hewitt Family',g)
    with pytest.raises(ValueError,match='active|default|only'):
        delete_family_file(db,active_family_file(db)['id'])
    set_default_family(db,wid)
    with pytest.raises(ValueError,match='default'):
        delete_family_file(db,wid)


def test_inactive_nondefault_family_can_be_deleted(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); g=ged(tmp_path/'a.ged')
    wid=register_family_file(db,'Hewitt Family',g)
    delete_family_file(db,wid)
    assert wid not in {x['id'] for x in list_family_files(db)}


def test_reports_are_owned_by_active_family_and_can_be_preserved_on_delete(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); ensure_family_files(db)
    active=active_family_file(db)
    report=tmp_path/'r.html'; report.write_text('x')
    _record(db,'Biography','Alpha',report,'HTML')
    assert publication_history(db)[0]['workspace_id']==active['id']
    assert family_report_count(db,active['id'])==1


def test_data_manager_exposes_management_actions(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); g=ged(tmp_path/'a.ged')
    register_family_file(db,'Hewitt Family 14',g)
    html=render_get(db,'/data',{})
    assert 'Rename' in html
    assert 'Make Default' in html
    assert 'Delete Family File' in html
    assert 'original GEDCOM/family file is not changed' in html
