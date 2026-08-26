from reunion_companion.companion.database import connect
from reunion_companion.companion import beta_ui


def test_research_page_orders_actionable_work_before_background(monkeypatch,tmp_path):
    db=connect(tmp_path/"x.db")

    import reunion_companion.companion.external_evidence_matcher as matcher
    import reunion_companion.companion.external_research_runner as runner
    import reunion_companion.companion.ryerson_targeted_bootstrap as targeted

    monkeypatch.setattr(matcher,"ryerson_death_candidates",lambda db:[])
    monkeypatch.setattr(runner,"runner_status",lambda db:{
        "enabled":False,"source_waiting":False,"queued":0,
        "retry_wait":0,"findings":0,"no_match":0,"failed":0,
    })
    monkeypatch.setattr(targeted,"targeted_status",lambda db:{
        "enabled":False,"completed":0,"queued":0,"retry_wait":0,
        "searching":0,"failed":0,"total":0,"core_surnames":["Knuckey"],
    })

    html=beta_ui.research_page(db)

    review=html.index("External Evidence Review")
    death=html.index("Ryerson Death Research")
    unsourced=html.index("Unsourced Events")
    background=html.index("Background Research")

    assert review < death < unsourced < background
    assert "<details" in html
    assert "Ryerson Targeted Bootstrap Runner" in html
