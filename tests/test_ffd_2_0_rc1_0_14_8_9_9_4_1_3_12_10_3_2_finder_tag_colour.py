from reunion_companion.companion import media_reconciliation as mr


class DB:
    def execute(self,*a,**k):
        class R:
            def fetchone(self): return None
            def fetchall(self): return []
        return R()


def test_not_referenced_finder_tag_is_red_and_preserves_existing_colours(monkeypatch, tmp_path):
    p = tmp_path / 'orphan.jpg'
    p.write_bytes(b'x')
    monkeypatch.setattr(mr, 'reconcile_media', lambda db: {'unreferenced': [{'path': str(p)}]})
    state = {str(p): ['Family\n2', 'Archive\n4']}
    labels = {str(p): 4}
    monkeypatch.setattr(mr, '_finder_tags', lambda path: list(state[str(path)]))
    monkeypatch.setattr(mr, '_write_finder_tags', lambda path, tags: state.__setitem__(str(path), list(tags)))
    monkeypatch.setattr(mr, '_finder_label_code', lambda path: labels[str(path)])
    monkeypatch.setattr(mr, '_set_finder_label_code', lambda path, value: labels.__setitem__(str(path), value))

    result = mr.set_not_referenced_finder_tags(DB())
    assert result['changed'] == 1
    assert state[str(p)] == ['Family\n2', 'Archive\n4', 'Reunion - Not Referenced\n1']
    assert labels[str(p)] == 1


def test_red_tag_matches_native_finder_observation():
    assert mr.NOT_REFERENCED_FINDER_COLOUR == 1
    assert mr._native_not_referenced_tag() == 'Reunion - Not Referenced\n1'
