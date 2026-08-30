from pathlib import Path

from reunion_companion.companion.ryerson_discovery_ui import sort_external_findings_recent_first


def test_candidate_cards_are_confidence_first_then_recent():
    findings=[
        {"id":1,"match_confidence":95,"event_date":"20JUL2012"},
        {"id":2,"match_confidence":55,"event_date":"25JUL2012"},
        {"id":3,"match_confidence":75,"event_date":"01JAN2026"},
        {"id":4,"match_confidence":95,"event_date":"21JUL2012"},
    ]
    got=sort_external_findings_recent_first(findings)
    assert [(r["match_confidence"],r["id"]) for r in got] == [(95,4),(95,1),(75,3),(55,2)]


def test_candidate_browser_sort_keeps_confidence_primary():
    src=Path("src/reunion_companion/companion/beta_ui.py").read_text()
    assert "if(ac!==bc)return bc-ac" in src
    assert "Confidence, then Most Recent Event Date" in src


def test_research_sections_render_only_bottom_pagers():
    src=Path("src/reunion_companion/companion/beta_ui.py").read_text()
    assert "if death_pages>1:\n        body+=death_pager" not in src
    assert "if quality_pages>1:\n        body+=quality_pager" not in src
    # Their bottom pager remains.
    assert "body+=death_pager" in src
    assert "body+=quality_pager" in src


def test_external_review_pagers_are_not_duplicated_at_top():
    src=Path("src/reunion_companion/companion/ryerson_discovery_ui.py").read_text()
    assert "out.append(review_pager)" in src  # bottom after list
    assert src.count("out.append(review_pager)") == 1
    assert "out.append(workspace_pager)" in src
    assert src.count("out.append(workspace_pager)") == 1
