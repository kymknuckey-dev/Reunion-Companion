from pathlib import Path

UI=Path("src/reunion_companion/companion/beta_ui.py")

def _text():
    return UI.read_text()

def test_manage_uses_one_primary_gedcom_refresh_action():
    text=_text()
    assert '>Safe Refresh GEDCOM</button>' in text
    assert 'Safe Refresh Current GEDCOM' not in text
    assert '<h2>Safe Refresh from New GEDCOM</h2>' not in text
    assert 'Choose Different GEDCOM…' in text

def test_manage_hides_full_import_history_but_keeps_latest_status():
    text=_text()
    assert 'LAST REFRESH' in text
    assert '<h2>Import History</h2>' not in text
    assert 'latest_history=import_history(db,limit=1)' in text

def test_manage_keeps_recent_crawler_activity_compact():
    text=_text()
    assert 'Recent crawler activity' in text
    assert 'rc-manage-activity' in text
