from reunion_companion.companion import media_reconciliation as mr


class DB:
    def execute(self,*a,**k):
        class R:
            def fetchone(self): return None
            def fetchall(self): return []
        return R()


def test_native_finder_tag_and_finderinfo_are_kept_in_sync(monkeypatch, tmp_path):
    p = tmp_path / 'orphan.jpg'
    p.write_bytes(b'x')
    monkeypatch.setattr(mr, 'reconcile_media', lambda db: {'unreferenced': [{'path': str(p)}]})
    state = {str(p): []}
    labels = {str(p): 0}
    monkeypatch.setattr(mr, '_finder_tags', lambda path: list(state[str(path)]))
    monkeypatch.setattr(mr, '_write_finder_tags', lambda path, tags: state.__setitem__(str(path), list(tags)))
    monkeypatch.setattr(mr, '_finder_label_code', lambda path: labels[str(path)])
    monkeypatch.setattr(mr, '_set_finder_label_code', lambda path, value: labels.__setitem__(str(path), value))

    r = mr.set_not_referenced_finder_tags(DB())
    assert r['changed'] == 1
    assert state[str(p)] == ['Reunion - Not Referenced\n1']
    assert labels[str(p)] == 1

    r = mr.set_not_referenced_finder_tags(DB(), remove=True)
    assert r['changed'] == 1
    assert state[str(p)] == []
    assert labels[str(p)] == 0
