from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PUB=(ROOT/"src/reunion_companion/companion/publishing_v11.py").read_text()

def test_birth_documents_use_dedicated_renderer():
    assert "def _birth_document_block" in PUB
    assert "class='birth-document-page" in PUB
    assert "birth-document-heading" in PUB
    assert "birth-document-preview" in PUB
    assert "birth-document-caption" in PUB

def test_first_birth_pdf_is_not_sent_through_normal_archive_renderer():
    block=PUB[PUB.index('if key=="birth":'):PUB.index('        else:',PUB.index('if key=="birth":'))]
    assert "_birth_document_block(first" in block

def test_first_birth_page_owns_heading_and_preview():
    block=PUB[PUB.index("def _birth_document_block"):PUB.index("def _publication_fact_sections")]
    assert "<h2 class='birth-document-heading'>Birth Documents</h2>" in block
    assert "len(pages)>1" in block
    assert "_multi_page_document_print_blocks" in block
    assert "birth-document-original" not in block

def test_dedicated_birth_page_is_printed_and_page_fitted():
    assert ".birth-document-page {" in PUB
    assert "height:258mm" in PUB
    assert "max-height:207mm" in PUB
    assert ".birth-document-page { display:block !important; }" in PUB
