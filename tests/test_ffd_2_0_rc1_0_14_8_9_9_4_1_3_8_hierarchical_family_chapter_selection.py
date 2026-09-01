from reunion_companion.companion.database import connect
from reunion_companion.companion.family_book_scope import build_scope
from reunion_companion.companion.beta_ui import book_scope_page


def person(db,pid,name,sex='M'):
    db.execute('INSERT INTO people(id,display_name,sex) VALUES(?,?,?)',(pid,name,sex))


def family(db,fid,h,w,kids=()):
    db.execute('INSERT INTO families(id) VALUES(?)',(fid,))
    if h: db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Husband')",(fid,h))
    if w: db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Wife')",(fid,w))
    for kid in kids: db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Child')",(fid,kid))


def seed(db):
    names={1:'Thomas',2:'Johanna',3:'James',4:'Sibling A',5:'Elizabeth',6:'Charles',7:'Sibling A Spouse',8:'Louisa',9:'Victor',10:'Lois',11:'Mervyn',12:'Brian',13:'Elaine',14:'Patricia',15:'Kym',16:'Susan',17:'Brian Child',18:'Brian Child Spouse',19:'Kym Child',20:'Kym Child Spouse',21:'Great Grandchild',22:'GG Spouse'}
    for pid,name in names.items(): person(db,pid,name,'F' if pid in {2,5,7,8,10,13,14,16,18,20,22} else 'M')
    family(db,100,1,2,(3,4))
    db.execute("INSERT INTO events(id,person_id,event_type,date_text) VALUES(9003,3,'Birth','10 JAN 1900')")
    db.execute("INSERT INTO events(id,person_id,event_type,date_text) VALUES(9004,4,'Birth','10 JAN 1898')")
    family(db,101,3,5,(6,))
    family(db,150,4,7,())
    family(db,102,6,8,(9,))
    family(db,103,9,10,(11,12))
    db.execute("INSERT INTO events(id,person_id,event_type,date_text) VALUES(9011,11,'Birth','1 JAN 1930')")
    db.execute("INSERT INTO events(id,person_id,event_type,date_text) VALUES(9012,12,'Birth','1 JAN 1932')")
    family(db,104,11,13,(15,))
    family(db,160,12,14,(17,))
    family(db,170,15,16,(19,))
    family(db,180,17,18,())
    family(db,190,19,20,(21,))
    family(db,200,21,22,())
    db.commit()


def test_selector_reaches_deep_side_branches_without_selecting_them(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db)
    scope=build_scope(db,1,11,4)
    ids={e.family_id for e in scope['entries']}
    assert {160,180,170,190,200} <= ids
    parents={e.family_id:e.parent_family_id for e in scope['entries']}
    assert parents[170]==104  # Kym family belongs beneath Mervyn's family.
    assert parents[160]==103  # Brian family belongs beneath Victor's family.
    assert scope['selected_family_ids']==[100,101,102,103,104]
    db.close()


def test_selected_chapters_keep_sibling_family_level_together_before_descending(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db)
    selected={100,101,150,102,103,104,160,170,180,190,200}
    scope=build_scope(db,1,11,4,selected)
    # Root Daughter is older than Line Son, so her family is first. At every
    # later parent family, all selected sibling families are emitted together
    # before publication descends into their children.  In particular Victor's
    # children Mervyn (104) and Brian (160) stay together before Kym (170).
    assert scope['selected_family_ids']==[100,150,101,102,103,104,160,170,190,200,180]
    db.close()


def test_selector_is_progressive_and_branch_opening_is_separate_from_selection(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db)
    html=book_scope_page(db,1,{'endpoint':'11'})
    assert "class='family-selector-branch'" in html
    assert '<details' in html and '<summary>' in html
    assert "name='family_180'" in html and "name='family_200'" in html
    assert 'opening a branch does not include it' in html
    # Only the root family is expanded initially; deeper paternal families are
    # deliberately opened one level at a time.
    assert html.count("<details class='family-selector-branch' open>")==1
    # Leaf and expandable sibling labels share the same horizontal alignment.
    assert ".family-selector-leaf{padding:10px 0}" in html
    # Deep side families are available but remain unchecked by default.
    frag=html.split("name='family_180'",1)[1][:80]
    assert 'checked' not in frag
    db.close()


def test_paternal_path_is_only_a_scope_construction_hint(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db)
    selected={100,101,150,102,103,104,160,170,180,190,200}
    normal=build_scope(db,1,11,4,selected)
    legacy_flag=build_scope(db,1,11,4,selected,True)
    # Retain the optional argument for compatibility, but publication order is
    # now birth-order family-level-first regardless of the old paternal-last flag.
    assert legacy_flag['selected_family_ids']==normal['selected_family_ids']
    db.close()


def test_family_history_selector_no_longer_exposes_paternal_path_last(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db)
    html=book_scope_page(db,1,{'endpoint':'11'})
    assert "name='paternal_path_last'" not in html
    assert 'Paternal path last' not in html
    db.close()
