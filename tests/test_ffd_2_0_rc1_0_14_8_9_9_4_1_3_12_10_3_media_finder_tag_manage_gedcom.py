from pathlib import Path
from reunion_companion.companion import media_reconciliation as mr
from reunion_companion.companion.beta_ui import media_reconciliation_page

class DB:
    def execute(self,*a,**k):
        class R:
            def fetchone(self): return None
            def fetchall(self): return []
        return R()

def test_finder_tag_preserves_other_tags(monkeypatch,tmp_path):
    p=tmp_path/'orphan.jpg'; p.write_bytes(b'x')
    monkeypatch.setattr(mr,'reconcile_media',lambda db:{'unreferenced':[{'path':str(p)}]})
    state={str(p):['Family','Blue\n4']}
    labels={str(p):4}
    monkeypatch.setattr(mr,'_finder_tags',lambda path:list(state.get(str(path),[])))
    monkeypatch.setattr(mr,'_write_finder_tags',lambda path,tags:state.__setitem__(str(path),list(tags)))
    monkeypatch.setattr(mr,'_finder_label_code',lambda path:labels.get(str(path),0))
    monkeypatch.setattr(mr,'_set_finder_label_code',lambda path,value:labels.__setitem__(str(path),value))
    r=mr.set_not_referenced_finder_tags(DB())
    assert r['changed']==1
    assert state[str(p)]==['Family','Blue\n4','Reunion - Not Referenced\n1']
    assert labels[str(p)]==1
    r=mr.set_not_referenced_finder_tags(DB(),remove=True)
    assert state[str(p)]==['Family','Blue\n4']
    assert labels[str(p)]==4

def test_media_page_has_explicit_finder_tag_actions(monkeypatch,tmp_path):
    p=tmp_path/'orphan.jpg'; p.write_bytes(b'x')
    monkeypatch.setattr('reunion_companion.companion.beta_ui.reconcile_media',lambda db:{'root':str(tmp_path),'root_exists':True,'counts':{'unreferenced':1},'unreferenced':[{'path':str(p),'name':p.name,'relative_path':p.name,'size':1}],'referenced_missing':[],'referenced_found':[],'cloud_placeholders':[]})
    html=media_reconciliation_page(DB(),{'view':'unreferenced'})
    assert 'Tag Not Referenced Files' in html
    assert 'Remove Finder Tag' in html
    assert 'Reunion - Not Referenced' in html

def test_manage_gedcom_has_no_permanent_change_source_control():
    text=Path('src/reunion_companion/companion/beta_ui.py').read_text()
    assert "<details class='rc-change-gedcom'>" not in text
    assert "<div class='rc-change-gedcom'><form" not in text
    assert 'Choose Different GEDCOM' not in text
    assert 'reunion-companion://locate-gedcom' in text
