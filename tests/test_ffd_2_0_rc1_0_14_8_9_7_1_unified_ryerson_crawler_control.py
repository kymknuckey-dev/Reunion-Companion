from pathlib import Path

from reunion_companion.companion import beta_ui
from reunion_companion.companion.database import connect


def test_manage_exposes_one_unified_ryerson_control(monkeypatch,tmp_path):
    db=connect(tmp_path/'x.db')
    import reunion_companion.companion.external_research_runner as runner
    import reunion_companion.companion.ryerson_targeted_bootstrap as targeted

    monkeypatch.setattr(runner,'runner_status',lambda db:{
        'enabled':False,'source_waiting':False,'total':6619,'queued':6610,'searching':0,
        'retry_wait':0,'findings':0,'no_match':0,'failed':9,
    })
    monkeypatch.setattr(targeted,'targeted_status',lambda db:{
        'enabled':False,'completed':200,'queued':5092,'retry_wait':1,
        'searching':0,'failed':28,'total':5321,'core_surnames':['Knuckey'],
    })

    html=beta_ui.data_page(db)
    assert 'Ryerson Crawler — Paused' in html
    assert "action='/manage/ryerson/start'" in html
    assert html.count('Start Ryerson Crawler') == 1
    assert 'Start Death Research' not in html
    assert 'Pause Death Research' not in html
    assert 'Death-research queue —' not in html
    assert 'Family-wide (paused):' in html
    assert 'Death research:' in html


def test_manage_running_when_death_research_engine_is_enabled(monkeypatch,tmp_path):
    db=connect(tmp_path/'x.db')
    import reunion_companion.companion.external_research_runner as runner
    import reunion_companion.companion.ryerson_targeted_bootstrap as targeted

    monkeypatch.setattr(runner,'runner_status',lambda db:{
        'enabled':True,'source_waiting':False,'total':9,'queued':4,'searching':0,
        'retry_wait':1,'findings':2,'no_match':1,'failed':1,
    })
    monkeypatch.setattr(targeted,'targeted_status',lambda db:{
        'enabled':False,'completed':200,'queued':5092,'retry_wait':1,
        'searching':0,'failed':28,'total':5321,'core_surnames':['Knuckey'],
    })

    html=beta_ui.data_page(db)
    assert 'Ryerson Crawler — Running' in html
    assert "action='/manage/ryerson/pause'" in html
    assert html.count('Pause Ryerson Crawler') == 1


def test_manage_routes_control_death_research_and_force_family_wide_paused():
    source=Path('src/reunion_companion/companion/beta_ui.py').read_text()
    assert '"/manage/ryerson/start","/manage/ryerson/pause"' in source
    block=source[source.index('if u.path in ("/manage/ryerson/start"'):source.index('if u.path in ("/research/ryerson/targeted/start"')]
    assert 'start_targeted_bootstrap(db)' not in block
    assert 'start_runner(db)' in block
    assert 'pause_targeted_bootstrap(db)' in block
    assert 'pause_runner(db)' in block
    assert 'recover_transport_failures(db)' in block


def test_legacy_internal_engine_routes_are_retained():
    source=Path('src/reunion_companion/companion/beta_ui.py').read_text()
    assert '"/research/ryerson/targeted/start"' in source
    assert '"/research/ryerson/targeted/pause"' in source
    assert '"/research/ryerson/runner/start"' in source
    assert '"/research/ryerson/runner/pause"' in source
