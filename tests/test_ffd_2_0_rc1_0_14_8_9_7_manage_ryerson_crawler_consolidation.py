from pathlib import Path

from reunion_companion.companion import beta_ui
from reunion_companion.companion.database import connect


def test_manage_owns_ryerson_crawler_controls(monkeypatch,tmp_path):
    db=connect(tmp_path/'x.db')
    import reunion_companion.companion.external_research_runner as runner
    import reunion_companion.companion.ryerson_targeted_bootstrap as targeted

    monkeypatch.setattr(runner,'runner_status',lambda db:{
        'enabled':False,'source_waiting':False,'total':9,'queued':4,'searching':0,
        'retry_wait':1,'findings':2,'no_match':1,'failed':1,
    })
    monkeypatch.setattr(targeted,'targeted_status',lambda db:{
        'enabled':False,'completed':200,'queued':5092,'retry_wait':1,
        'searching':0,'failed':28,'total':5321,'core_surnames':['Knuckey'],
    })

    html=beta_ui.data_page(db)
    assert '<h2>Ryerson Crawler</h2>' in html
    assert 'Ryerson Crawler — Paused' in html
    assert 'Completed 200' in html
    assert 'Queued 5092' in html
    assert 'Waiting 1' in html
    assert 'Searching 0' in html
    assert 'Failed 28' in html
    assert 'Total 5321' in html
    assert 'Core Knuckey' in html
    assert "action='/manage/ryerson/start'" in html
    assert '>Start Ryerson Crawler<' in html
    assert 'Death research:' in html
    assert 'Start Death Research' not in html


def test_research_page_is_evidence_review_not_crawler_management(monkeypatch,tmp_path):
    db=connect(tmp_path/'x.db')
    import reunion_companion.companion.external_evidence_matcher as matcher
    monkeypatch.setattr(matcher,'missing_death_candidates',lambda db:[])

    html=beta_ui.research_page(db)
    assert 'External Evidence Review' in html
    assert 'Ryerson Research Runner' not in html
    assert 'Targeted Bootstrap' not in html
    assert 'Background Research' not in html
    assert 'Start Ryerson Crawler' not in html
    assert 'Pause Ryerson Crawler' not in html
    assert "action='/research/ryerson/targeted/start'" not in html
    assert "action='/research/ryerson/runner/start'" not in html


def test_legacy_engine_routes_are_retained_internally():
    source=Path('src/reunion_companion/companion/beta_ui.py').read_text()
    assert '"/research/ryerson/targeted/start"' in source
    assert '"/research/ryerson/targeted/pause"' in source
    assert '"/research/ryerson/runner/start"' in source
    assert '"/research/ryerson/runner/pause"' in source
    assert 'start_targeted_bootstrap' in source
    assert 'pause_targeted_bootstrap' in source
    assert 'start_runner' in source
    assert 'pause_runner' in source
