import sqlite3
from reunion_companion.companion.database import SCHEMA
from reunion_companion.companion.family_book_scope import build_structure_scope
from reunion_companion.companion.beta_ui import book_scope_page


def _db():
    d=sqlite3.connect(':memory:'); d.row_factory=sqlite3.Row; d.executescript(SCHEMA)
    return d


def _person(d,pid,name):
    d.execute("INSERT INTO people(id,gedcom_xref,display_name) VALUES(?,?,?)",(pid,f'@I{pid}@',name))

def _family(d,fid,h,w,children=()):
    d.execute("INSERT INTO families(id,gedcom_xref) VALUES(?,?)",(fid,f'@F{fid}@'))
    if h:d.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Husband')",(fid,h))
    if w:d.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Wife')",(fid,w))
    for c in children:d.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Child')",(fid,c))


def test_structure_scope_orders_each_selected_branch_before_next_sibling():
    d=_db()
    for pid,name in [(1,'Root'),(2,'Spouse'),(3,'Older'),(4,'Younger'),(5,'A'),(6,'B'),(7,'C'),(8,'D')]:_person(d,pid,name)
    _family(d,10,1,2,[3,4]); _family(d,20,3,5,[7]); _family(d,30,7,8,[]); _family(d,40,4,6,[])
    d.execute("INSERT INTO events(person_id,event_type,date_text) VALUES(3,'Birth','1900')")
    d.execute("INSERT INTO events(person_id,event_type,date_text) VALUES(4,'Birth','1910')")
    scope=build_structure_scope(d,1,{10,20,30,40})
    assert scope['selected_family_ids']==[10,20,30,40]


def test_family_history_ui_has_no_paternal_endpoint_or_branch_order_control():
    d=_db(); _person(d,1,'Root'); _person(d,2,'Spouse'); _family(d,10,1,2,[])
    html=book_scope_page(d,1,{})
    assert 'paternal-line endpoint' not in html
    assert 'Branch ordering starts here' not in html
    assert 'genealogical family order' in html
