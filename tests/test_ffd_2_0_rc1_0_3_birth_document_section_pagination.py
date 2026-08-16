from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = (ROOT / "src/reunion_companion/companion/publishing_v11.py").read_text()

from pathlib import Path
from reunion_companion import app_identity
from reunion_companion.companion import publishing_v11 as pub

def test_release_identity():
    assert app_identity.APP_RELEASE_DISPLAY == "FFD 2.0 RC1.0.3"
    assert app_identity.APP_RELEASE_NAME == "Birth Document Fitted Page Structural Repair"
    assert app_identity.ENGINE_BASELINE == "FFD 1.9 RC1"

def test_birth_documents_section_starts_new_print_page():
    # RC1.0.3 structural repair: the dedicated first Birth Documents page
    # owns the page break rather than the outer document section.
    assert ".birth-document-page {" in PUB
    assert "break-before:page;" in PUB
    assert "page-break-before:always;" in PUB
    assert "def _birth_document_block" in PUB

def test_page_break_is_birth_specific_not_all_document_sections():
    # Only the first Birth Documents PDF uses the dedicated fitted-page
    # renderer. Other document groups continue through _media_block.
    assert '_birth_document_block(first' in PUB
    assert 'if key=="birth":' in PUB
    assert 'for m in groups[key]:' in PUB
    assert 'P.append(_media_block(m,output_html,person_name=p["display_name"],db=db))' in PUB

def test_existing_media_pagination_repairs_remain():
    css=pub.PRO_CSS
    assert ".photo-page.landscape-pair" in css
    assert "figure.media-card.media-portrait" in css
    assert "max-height:198mm !important" in css
