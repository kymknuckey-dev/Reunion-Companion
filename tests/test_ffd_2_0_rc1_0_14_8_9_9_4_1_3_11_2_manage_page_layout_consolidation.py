from pathlib import Path

from reunion_companion.companion import beta_ui
from reunion_companion.companion.database import connect


def _stub_status(monkeypatch):
    import reunion_companion.companion.external_research_runner as runner
    import reunion_companion.companion.ryerson_targeted_bootstrap as targeted
    monkeypatch.setattr(runner,'runner_status',lambda db:{
        'enabled':False,'source_waiting':False,'total':0,'queued':0,'searching':0,
        'retry_wait':0,'findings':0,'no_match':0,'failed':0,
    })
    monkeypatch.setattr(targeted,'targeted_status',lambda db:{
        'enabled':False,'completed':0,'queued':0,'retry_wait':0,
        'searching':0,'failed':0,'total':0,'core_surnames':['Knuckey'],
    })


def test_manage_layout_consolidation_survives_workflow_simplification(monkeypatch,tmp_path):
    db=connect(tmp_path/'manage.sqlite3')
    _stub_status(monkeypatch)
    monkeypatch.setattr(beta_ui,'_ryerson_recent_activity',lambda db,limit=3:[
        {'time':'07:12','name':'William Bailey','status':'Completed','outcome':'No finding'},
    ])
    html=beta_ui.data_page(db)

    # The three conceptual sections introduced by .11.2 remain.
    assert '<h2>Family Files</h2>' in html
    assert '<h2>Reunion GEDCOM</h2>' in html
    assert '<h2>Ryerson Crawler</h2>' in html
    assert 'William Bailey' in html

    # .12 deliberately simplified the GEDCOM workflow.
    assert 'Safe Refresh GEDCOM' in html
    assert 'Choose Different GEDCOM' not in html
    assert 'EXPECTED GEDCOM' in html
    assert 'LAST REFRESH' in html
    assert "class='rc-manage-history'" not in html
    assert '<h2>Import History</h2>' not in html


def test_manage_history_is_deliberately_not_exposed_after_workflow_consolidation(monkeypatch,tmp_path):
    db=connect(tmp_path/'manage.sqlite3')
    _stub_status(monkeypatch)
    monkeypatch.setattr(beta_ui,'_ryerson_recent_activity',lambda db,limit=3:[])
    html=beta_ui.data_page(db,import_page=2)
    assert 'LAST REFRESH' in html
    assert "class='rc-manage-history'" not in html
    assert 'Page 2 of' not in html


def test_historical_release_identity_manage_page_layout_consolidation_is_preserved():
    source=Path('macos_app/build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.11.2 — Manage Page Layout Consolidation"' in source
