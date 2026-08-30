from pathlib import Path

from reunion_companion.companion import beta_ui
from reunion_companion.companion.database import connect


def _runner(enabled=False):
    return {
        'enabled': enabled, 'source_waiting': False, 'total': 6619, 'queued': 6191,
        'searching': 0, 'retry_wait': 0, 'findings': 28, 'no_match': 86, 'failed': 310,
    }


def _family(enabled=True):
    return {
        'enabled': enabled, 'completed': 602, 'queued': 4678, 'retry_wait': 0,
        'searching': 0, 'failed': 41, 'total': 5321, 'core_surnames': ['Knuckey'],
    }


def test_manage_state_is_driven_only_by_death_research(monkeypatch, tmp_path):
    db=connect(tmp_path/'x.db')
    import reunion_companion.companion.external_research_runner as runner
    import reunion_companion.companion.ryerson_targeted_bootstrap as targeted
    monkeypatch.setattr(runner,'runner_status',lambda db:_runner(False))
    monkeypatch.setattr(targeted,'targeted_status',lambda db:_family(True))
    html=beta_ui.data_page(db)
    assert 'Ryerson Crawler — Paused' in html
    assert 'Family-wide (paused):' in html
    assert 'surname + first given name' in html
    assert "action='/manage/ryerson/start'" in html


def test_manage_route_never_starts_family_wide_engine():
    source=Path('src/reunion_companion/companion/beta_ui.py').read_text()
    block=source[source.index('if u.path in ("/manage/ryerson/start"'):source.index('if u.path in ("/research/ryerson/targeted/start"')]
    assert 'start_targeted_bootstrap(db)' not in block
    assert 'pause_targeted_bootstrap(db)' in block
    assert 'start_runner(db)' in block
    assert 'pause_runner(db)' in block
    assert 'recover_transport_failures(db)' in block


def test_app_startup_clears_persisted_family_wide_enabled_flag():
    source=Path('src/reunion_companion/companion/beta_ui.py').read_text()
    startup=source[source.index('from .external_research_runner import start_background_runner'):]
    assert 'pause_targeted_bootstrap(_crawler_db)' in startup
    assert 'start_background_targeted_bootstrap(' in startup


def test_legacy_family_wide_routes_and_queue_machinery_are_retained():
    source=Path('src/reunion_companion/companion/beta_ui.py').read_text()
    assert '"/research/ryerson/targeted/start"' in source
    assert '"/research/ryerson/targeted/pause"' in source
    assert 'start_targeted_bootstrap(db)' in source
    assert 'pause_targeted_bootstrap(db)' in source
