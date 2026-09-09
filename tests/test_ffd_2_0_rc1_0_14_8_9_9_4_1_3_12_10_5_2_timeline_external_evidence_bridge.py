"""Compatibility contract for the superseded Timeline evidence bridge.

The accepted .12.10.5.2 design keeps the factual Timeline clean and surfaces
unactioned external evidence in the Current Person header instead.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_superseded_timeline_bridge_is_replaced_by_current_person_header_indicator():
    beta_ui = (ROOT / "src/reunion_companion/companion/beta_ui.py").read_text()
    story = (ROOT / "src/reunion_companion/companion/ffd_person_story.py").read_text()
    assert "def _unactioned_external_evidence_for_event" not in beta_ui
    assert "def _unactioned_external_evidence_count" in story
    assert "External evidence" in story
    assert "to review" in story
