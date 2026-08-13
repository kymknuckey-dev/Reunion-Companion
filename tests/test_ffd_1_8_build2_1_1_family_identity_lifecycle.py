from pathlib import Path
import json
import pytest

from reunion_companion.companion.database import connect
from reunion_companion.companion.family_files import (
    active_family_file, list_family_files, register_family_file, set_active_family,
    set_default_family, delete_family_file, preflight_family_refresh,
    FamilyFileMismatch,
)
from reunion_companion.companion.beta_ui import family_mismatch_body, render_get


def ged(path, names, source='Reunion'):
    lines=['0 HEAD',f'1 SOUR {source}']
    for i,name in enumerate(names,1):
        first,last=name.split()[0],name.split()[-1]
        lines += [f'0 @I{i}@ INDI',f'1 NAME {first} /{last}/','1 SEX M','1 BIRT',f'2 DATE {i} JAN 1900']
    lines += ['0 TRLR']
    path.write_text('\n'.join(lines)+'\n')
    return path


def test_switching_family_identity_never_rewrites_fingerprint_or_import_history(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    kn=ged(tmp_path/'kn.ged',['Kym Knuckey','Mervyn Knuckey'])
    hew=ged(tmp_path/'hew.ged',['Scott Beatty','Gordon Stock'])
    # Turn initial legacy workspace into a controlled Knuckey identity.
    ff=active_family_file(db)
    from reunion_companion.companion.family_files import record_workspace_import
    record_workspace_import(db,ff['id'],kn)
    hw=register_family_file(db,'Hewitt Family',hew,'Reunion')
    before={x['id']:(x['fingerprint_json'],x['gedcom_path']) for x in list_family_files(db)}
    imports_before=db.execute('SELECT COUNT(*) FROM companion_family_imports').fetchone()[0]
    set_active_family(db,hw); set_active_family(db,ff['id']); set_active_family(db,hw)
    after={x['id']:(x['fingerprint_json'],x['gedcom_path']) for x in list_family_files(db)}
    assert before==after
    assert db.execute('SELECT COUNT(*) FROM companion_family_imports').fetchone()[0]==imports_before


def test_wrong_gedcom_still_rejected_after_repeated_switching_and_default_changes(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    kn=ged(tmp_path/'kn.ged',['Kym Knuckey','Mervyn Knuckey','Elaine Cox'])
    hew=ged(tmp_path/'hew.ged',['Scott Beatty','Gordon Stock','Ada Hewitt'])
    from reunion_companion.companion.family_files import record_workspace_import
    kn_id=active_family_file(db)['id']; record_workspace_import(db,kn_id,kn)
    hw=register_family_file(db,'Hewitt Family',hew,'Reunion')
    for wid in (hw,kn_id,hw,kn_id): set_active_family(db,wid)
    set_default_family(db,hw); set_default_family(db,kn_id)
    with pytest.raises(FamilyFileMismatch) as ex:
        preflight_family_refresh(db,hew)
    assert ex.value.workspace['id']==kn_id
    assert ex.value.match['classification']=='likely_different'


def test_current_refresh_preflight_uses_active_family_recorded_source(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    kn=ged(tmp_path/'kn.ged',['Kym Knuckey','Mervyn Knuckey'])
    from reunion_companion.companion.family_files import record_workspace_import
    wid=active_family_file(db)['id']; record_workspace_import(db,wid,kn)
    result=preflight_family_refresh(db)
    assert result['workspace']['id']==wid
    assert Path(result['path'])==kn.resolve()
    assert result['verdict']['match']['classification']=='confident_match'


def test_delete_default_and_active_lifecycle_promotes_survivor(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    hew=ged(tmp_path/'hew.ged',['Scott Beatty','Gordon Stock'])
    original=active_family_file(db)['id']
    hw=register_family_file(db,'Hewitt Family',hew,'Reunion')
    # Default can be deleted; survivor becomes default and active remains valid.
    result=delete_family_file(db,original)
    assert result['replacement']['id']==hw
    ff=active_family_file(db)
    assert ff['id']==hw and ff['is_default']==1


def test_delete_nondefault_is_available_in_management_ui(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    hew=ged(tmp_path/'hew.ged',['Scott Beatty'])
    register_family_file(db,'Hewitt Family',hew,'Reunion')
    html=render_get(db,'/data',{})
    assert html.count('Delete Family File')>=2


def test_mismatch_screen_contains_real_add_family_form_with_selected_path(tmp_path):
    incoming=tmp_path/'Hewitt Family.ged'; incoming.write_text('0 HEAD\n0 TRLR\n')
    html=family_mismatch_body('Knuckey Family History',0.01,incoming)
    assert 'Add as a New Family File' in html
    assert "action='/family-file/add'" in html
    assert str(incoming) in html
    assert 'Nothing has been changed' in html
