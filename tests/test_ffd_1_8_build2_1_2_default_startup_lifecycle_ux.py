from pathlib import Path

from reunion_companion.companion.database import connect
from reunion_companion.companion.family_files import (
    active_family_file, register_family_file, set_active_family, set_default_family,
    list_family_files,
)
from reunion_companion.companion import beta_ui
from reunion_companion.companion.beta_ui import render_get


def ged(path, name):
    first,last=name.split()[0],name.split()[-1]
    path.write_text(f"0 HEAD\n1 SOUR Reunion\n0 @I1@ INDI\n1 NAME {first} /{last}/\n1 SEX M\n0 TRLR\n")
    return path


def test_saved_default_is_activated_on_next_startup(tmp_path, monkeypatch):
    db_path=tmp_path/'x.sqlite3'; db=connect(db_path)
    kn=ged(tmp_path/'kn.ged','Kym Knuckey'); hew=ged(tmp_path/'hew.ged','Scott Hewitt')
    from reunion_companion.companion.family_files import record_workspace_import
    kn_id=active_family_file(db)['id']; record_workspace_import(db,kn_id,kn)
    hew_id=register_family_file(db,'Hewitt Family History',hew,'Reunion')
    set_default_family(db,hew_id)
    set_active_family(db,kn_id)
    db.close()

    materialised=[]
    monkeypatch.setattr(beta_ui,'staged_import',lambda dbp,path: materialised.append(Path(path).resolve()) or {'promoted':True})
    assert beta_ui._activate_default_family_on_startup(db_path) is True
    assert materialised==[hew.resolve()]
    db=connect(db_path)
    assert active_family_file(db)['id']==hew_id
    assert next(x for x in list_family_files(db) if x['id']==hew_id)['is_default']==1
    db.close()


def test_startup_does_nothing_when_default_is_already_active(tmp_path, monkeypatch):
    db_path=tmp_path/'x.sqlite3'; db=connect(db_path)
    assert active_family_file(db)['is_default']==1
    db.close()
    monkeypatch.setattr(beta_ui,'staged_import',lambda *a,**k: (_ for _ in ()).throw(AssertionError('must not materialise')))
    assert beta_ui._activate_default_family_on_startup(db_path) is False


def test_three_family_delete_confirmation_describes_real_lifecycle(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    h=register_family_file(db,'Hewitt Family History',ged(tmp_path/'h.ged','Scott Hewitt'),'Reunion')
    s=register_family_file(db,'Smith Family History',ged(tmp_path/'s.ged','Alex Smith'),'Reunion')
    kn=active_family_file(db)['id']
    set_default_family(db,h)
    set_active_family(db,s)
    html=render_get(db,'/data',{})
    # Inactive default: tells the user which surviving family becomes default, but not that it is currently open.
    assert 'Hewitt Family History is the default Family File.' in html
    assert 'Hewitt Family History is currently open.' not in html
    # Active non-default: tells the user Companion will switch away before deletion.
    assert 'Smith Family History is currently open.' in html
    # An ordinary inactive/non-default family gets no misleading active/default language.
    assert 'Delete Knuckey Family History from Reunion Companion?' in html
    db.close()
