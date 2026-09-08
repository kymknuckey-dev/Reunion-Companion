from pathlib import Path
from reunion_companion.companion import media_reconciliation as mr


class DB:
    def execute(self,*a,**k):
        class R:
            def fetchone(self): return None
            def fetchall(self): return []
        return R()


def test_native_red_tag_matches_finder_observed_encoding():
    assert mr.NOT_REFERENCED_FINDER_COLOUR == 1
    assert mr._native_not_referenced_tag() == 'Reunion - Not Referenced\n1'


def test_finderinfo_red_label_matches_observed_0002(monkeypatch,tmp_path):
    p=tmp_path/'x.jpg'; p.write_bytes(b'x')
    store={mr.FINDER_INFO_XATTR: bytes(32)}
    monkeypatch.setattr(mr,'_xattr_read',lambda path,name: store.get(name))
    monkeypatch.setattr(mr,'_xattr_write',lambda path,name,raw: store.__setitem__(name,raw))
    mr._set_finder_label_code(p,1)
    assert store[mr.FINDER_INFO_XATTR][8:10] == b'\x00\x02'
    assert mr._finder_label_code(p) == 1


def test_apply_and_remove_sync_named_tag_and_finderinfo(monkeypatch,tmp_path):
    p=tmp_path/'orphan.jpg'; p.write_bytes(b'x')
    monkeypatch.setattr(mr,'reconcile_media',lambda db:{'unreferenced':[{'path':str(p)}]})
    tags={str(p):['Family','Blue\n4']}
    labels={str(p):4}
    monkeypatch.setattr(mr,'_finder_tags',lambda path:list(tags.get(str(path),[])))
    monkeypatch.setattr(mr,'_write_finder_tags',lambda path,value:tags.__setitem__(str(path),list(value)))
    monkeypatch.setattr(mr,'_finder_label_code',lambda path:labels.get(str(path),0))
    monkeypatch.setattr(mr,'_set_finder_label_code',lambda path,value:labels.__setitem__(str(path),value))

    result=mr.set_not_referenced_finder_tags(DB())
    assert result['changed']==1
    assert tags[str(p)]==['Family','Blue\n4','Reunion - Not Referenced\n1']
    assert labels[str(p)]==1

    result=mr.set_not_referenced_finder_tags(DB(),remove=True)
    assert result['changed']==1
    assert tags[str(p)]==['Family','Blue\n4']
    assert labels[str(p)]==4


def test_remove_with_no_other_coloured_tag_clears_label_bits(monkeypatch,tmp_path):
    p=tmp_path/'orphan.jpg'; p.write_bytes(b'x')
    monkeypatch.setattr(mr,'reconcile_media',lambda db:{'unreferenced':[{'path':str(p)}]})
    tags={str(p):['Family','Reunion - Not Referenced\n1']}
    labels={str(p):1}
    monkeypatch.setattr(mr,'_finder_tags',lambda path:list(tags.get(str(path),[])))
    monkeypatch.setattr(mr,'_write_finder_tags',lambda path,value:tags.__setitem__(str(path),list(value)))
    monkeypatch.setattr(mr,'_finder_label_code',lambda path:labels.get(str(path),0))
    monkeypatch.setattr(mr,'_set_finder_label_code',lambda path,value:labels.__setitem__(str(path),value))
    mr.set_not_referenced_finder_tags(DB(),remove=True)
    assert tags[str(p)]==['Family']
    assert labels[str(p)]==0
