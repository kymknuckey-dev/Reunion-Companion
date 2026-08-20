from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PUB=(ROOT/"src/reunion_companion/companion/publishing_v11.py").read_text()
IDENT=(ROOT/"src/reunion_companion/app_identity.py").read_text()

def test_landscape_pair_is_vertical_not_side_by_side():
    assert "grid-template-rows:113mm 113mm" in PUB
    assert "grid-template-columns:repeat(2" not in PUB
    assert "max-height:91mm" in PUB

def test_portrait_atomic_page_reserves_caption_space():
    assert "height:113mm" in PUB
    assert ".photo-page .media-card figcaption { margin:0;" in PUB
    assert "display:flex" in PUB
    assert "align-items:center" in PUB
    assert "width:100%" in PUB

def test_children_use_shared_name_date_hierarchy():
    assert "class='person-name'" in PUB
    assert "class='person-dates'" in PUB
    assert "font-size:0.84em" in PUB
    assert "font-weight:400" in PUB

def test_descendant_chart_output_is_normalised_for_publication():
    assert "def _publication_person_typography" not in PUB
    assert "from .descendant_chart import chart_html" in PUB

def test_pdf_only_uses_temporary_html_and_assets():
    block=PUB[PUB.index("def write_book_pdf"):PUB.index("def format_publish_capabilities")]
    assert "TemporaryDirectory" in block
    assert 'pdf.with_suffix(".html")' not in block
    assert "write_book(db,start_pid,html" in block

def test_rc102_identity():
    assert 'APP_STAGE = "RC1.0.3"' in IDENT
    assert 'APP_RELEASE_NAME = "Birth Document Fitted Page Structural Repair"' in IDENT
    assert 'ENGINE_BASELINE = "FFD 1.9 RC1"' in IDENT
