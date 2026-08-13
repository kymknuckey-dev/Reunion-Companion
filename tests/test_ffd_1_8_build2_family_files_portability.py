from reunion_companion.companion.database import connect
from reunion_companion.companion.family_files import active_family_file,list_family_files,register_family_file,verify_refresh_for_workspace
from reunion_companion.companion.beta_ui import render_get

def ged(path,name='Alpha Person',xref='@I1@'):
    path.write_text(f'''0 HEAD\n1 SOUR Reunion\n0 {xref} INDI\n1 NAME {name.split()[0]} /{name.split()[-1]}/\n1 SEX M\n1 BIRT\n2 DATE 1 JAN 1900\n0 TRLR\n''')
    return path

def test_existing_database_gets_default_family_file(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    ff=active_family_file(db)
    assert ff['display_name']=='Knuckey Family History'
    assert ff['is_default']==1 and ff['is_active']==1

def test_duplicate_gedcom_ids_are_namespaced_by_family_file_registry(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); a=ged(tmp_path/'a.ged','Alpha One'); b=ged(tmp_path/'b.ged','Beta Two')
    x=register_family_file(db,'Alpha Family',a,'Reunion'); y=register_family_file(db,'Beta Family',b,'RootsMagic')
    assert x!=y
    rows=list_family_files(db)
    assert {'Alpha Family','Beta Family'} <= {r['display_name'] for r in rows}

def test_wrong_gedcom_is_classified_as_different(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); a=ged(tmp_path/'a.ged','Alpha One'); wid=register_family_file(db,'Alpha Family',a)
    # Make a substantially different incoming file with different identities.
    b=tmp_path/'b.ged'; b.write_text('0 HEAD\n1 SOUR Other\n'+''.join(f'0 @I{i}@ INDI\n1 NAME Person{i} /Other/\n1 BIRT\n2 DATE 1 JAN 19{i:02d}\n' for i in range(1,20))+'0 TRLR\n')
    v=verify_refresh_for_workspace(db,wid,b)
    assert v['match']['classification']=='likely_different'

def test_home_uses_active_family_title_and_selector_contract(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    html=render_get(db,'/',{})
    assert 'Knuckey Family History' in html

def test_data_manager_exposes_add_family_file(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); html=render_get(db,'/data',{})
    assert 'Family Files' in html and 'Add Family File' in html
