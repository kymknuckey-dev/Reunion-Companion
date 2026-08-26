from reunion_companion.companion.database import connect
from reunion_companion.companion import beta_ui


def test_compact_death_research_retains_missing_vs_incomplete(monkeypatch,tmp_path):
    db=connect(tmp_path/"x.db")

    import reunion_companion.companion.external_evidence_matcher as matcher
    import reunion_companion.companion.external_research_runner as runner
    import reunion_companion.companion.ryerson_targeted_bootstrap as targeted
    import reunion_companion.companion.ryerson_person_finding_bridge as bridge

    monkeypatch.setattr(matcher,"ryerson_death_candidates",lambda db:[
        {
            "person_id":1,"display_name":"Missing Person","gedcom_xref":"@I1@",
            "birth_date":"","birth_place":"","death_state":"missing",
            "death_note_text":"",
        },
        {
            "person_id":2,"display_name":"Incomplete Person","gedcom_xref":"@I2@",
            "birth_date":"","birth_place":"","death_state":"incomplete",
            "death_note_text":"note",
        },
    ])
    monkeypatch.setattr(runner,"runner_status",lambda db:{
        "enabled":False,"source_waiting":False,"queued":0,
        "retry_wait":0,"findings":0,"no_match":0,"failed":0,
    })
    monkeypatch.setattr(targeted,"targeted_status",lambda db:{
        "enabled":False,"completed":0,"queued":0,"retry_wait":0,
        "searching":0,"failed":0,"total":0,"core_surnames":["Knuckey"],
    })
    monkeypatch.setattr(bridge,"materialize_person_level_ryerson_findings",lambda db:{"assembled_count":0})

    html=beta_ui.research_page(db)
    assert "Research Needed" in html
    assert "Death missing" in html
    assert "Death incomplete" in html
