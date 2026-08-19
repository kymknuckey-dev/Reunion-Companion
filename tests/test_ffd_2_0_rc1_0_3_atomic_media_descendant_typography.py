from pathlib import Path
from reunion_companion import app_identity
from reunion_companion.companion import publishing_v11 as pub
from reunion_companion.companion.publishing_v7 import default_report_dir

def test_rc103_identity():
    assert app_identity.APP_RELEASE_DISPLAY=="FFD 2.0 RC1.0.3"
    assert app_identity.APP_RELEASE_NAME=="Birth Document Fitted Page Structural Repair"
    assert app_identity.ENGINE_BASELINE=="FFD 1.9 RC1"

def test_portrait_media_is_atomic_and_reserves_related_text_room():
    css=pub.PRO_CSS
    assert "figure.media-card.media-portrait" in css
    assert "max-height:198mm !important" in css
    assert ".media-card .open-original" not in css
    assert "page-break-inside:avoid" in css

def test_accepted_two_slot_vertical_photo_layout_is_preserved():
    css=pub.PRO_CSS
    assert ".photo-page.photo-pair" in css
    assert "max-height:91mm" in css
    assert "grid-template-rows:113mm 113mm" in css

def test_descendant_typography_is_semantic_not_regex_rewritten():
    root=Path(__file__).resolve().parents[1]
    pubsrc=(root/"src/reunion_companion/companion/publishing_v11.py").read_text()
    charts=(root/"src/reunion_companion/companion/descendant_chart.py").read_text()
    assert "def _publication_person_typography" not in pubsrc
    assert "from .descendant_chart import chart_html" in pubsrc
    assert "class='person-name'" in charts
    assert "class='person-dates'" in charts
    assert "spouses=[_named_person_html" in charts

def test_report_directory_isolates_automated_publication(monkeypatch,tmp_path):
    monkeypatch.setenv("REUNION_COMPANION_REPORT_DIR",str(tmp_path/"reports"))
    assert default_report_dir()==tmp_path/"reports"
