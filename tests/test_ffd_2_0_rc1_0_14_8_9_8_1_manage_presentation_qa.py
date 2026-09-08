from pathlib import Path


def _text():
    return Path('src/reunion_companion/companion/beta_ui.py').read_text()


def test_manage_uses_one_primary_gedcom_refresh_action():
    text=_text()
    assert '>Safe Refresh GEDCOM</button>' in text
    assert 'Safe Refresh Current GEDCOM' not in text
    assert '<h2>Safe Refresh from New GEDCOM</h2>' not in text
    assert 'Choose Different GEDCOM' not in text
    assert 'EXPECTED GEDCOM' in text
    assert 'Locate GEDCOM…' in text
