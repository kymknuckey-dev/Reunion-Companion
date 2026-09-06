from reunion_companion.companion.database import connect
from reunion_companion.companion.family_book_scope import build_scope
from reunion_companion.companion.beta_ui import book_scope_page
from reunion_companion.companion.report_configurations import save_report_configuration

from test_ffd_2_0_rc1_0_14_8_9_9_4_1_3_8_hierarchical_family_chapter_selection import seed, person, family


def extend_mervyn_children(db):
    for pid, name, sex in [
        (23, 'Jodie', 'F'), (24, 'Stuart', 'M'),
        (25, 'Jamie', 'F'), (26, 'Rachel', 'F'),
        (27, 'Jodie Child', 'F'), (28, 'Jodie Child Spouse', 'M'),
    ]:
        person(db, pid, name, sex)
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(104,23,'Child')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(104,25,'Child')")
    db.execute("INSERT INTO events(id,person_id,event_type,date_text) VALUES(9023,23,'Birth','1 JAN 1932')")
    db.execute("INSERT INTO events(id,person_id,event_type,date_text) VALUES(9025,25,'Birth','1 JAN 1934')")
    db.execute("INSERT INTO events(id,person_id,event_type,date_text) VALUES(9015,15,'Birth','1 JAN 1930')")
    family(db,210,23,24,(27,))
    family(db,220,25,26,())
    family(db,230,28,27,())
    db.commit()


def test_branch_order_changeover_keeps_history_grouped_then_follows_each_child_branch(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db); extend_mervyn_children(db)
    selected={100,101,150,102,103,104,160,170,180,190,200,210,220,230}

    historical=build_scope(db,1,11,4,selected)
    assert historical['selected_family_ids']==[100,150,101,102,103,104,160,170,210,220,190,200,230,180]

    hybrid=build_scope(db,1,11,4,selected,False,104)
    # Above Mervyn (104), sibling-family levels stay together: Mervyn and Brian
    # are both emitted before either branch is followed. From Mervyn downward,
    # each child branch is completed in birth order: Kym, Jodie, Jamie.
    assert hybrid['selected_family_ids']==[100,150,101,102,103,104,160,170,190,200,210,230,220,180]
    db.close()


def test_none_changeover_preserves_corrected_6_family_level_order(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db); extend_mervyn_children(db)
    selected={100,101,150,102,103,104,160,170,180,190,200,210,220,230}
    assert build_scope(db,1,11,4,selected,False,None)['selected_family_ids'] == build_scope(db,1,11,4,selected)['selected_family_ids']
    db.close()


def test_family_history_page_exposes_single_changeover_selector(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db); extend_mervyn_children(db)
    html=book_scope_page(db,1,{'endpoint':'11'})
    assert "name='branch_order_start_family_id'" not in html
    assert 'Branch ordering starts here' not in html
    assert 'genealogical family order' in html
    assert 'Mervyn and Elaine' in html
    db.close()


def test_saved_family_history_configuration_restores_changeover_family(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db); extend_mervyn_children(db)
    config_id=save_report_configuration(
        db,'family_history',1,'Dad book',
        {'endpoint':11,'selected_family_ids':[100,101,102,103,104,170],
         'format':'HTML','branch_order_start_family_id':104},
    )
    html=book_scope_page(db,1,{'config':str(config_id)})
    assert "name='branch_order_start_family_id'" not in html
    assert "name='family_104' value='1' checked" in html
    db.close()
