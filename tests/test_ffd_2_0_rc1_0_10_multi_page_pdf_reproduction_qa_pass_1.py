from pathlib import Path
import pytest
from reunion_companion.companion import publishing_v11 as pub


def _two_page_pdf(tmp_path):
    fitz=pytest.importorskip("pymupdf")
    pdf=tmp_path/"The memories of Mervyn Neil Knuckey.pdf"
    doc=fitz.open()
    for n in (1,2):
        page=doc.new_page(width=595,height=842)
        page.insert_text((72,100),f"Memories page {n}")
    doc.save(pdf); doc.close()
    return pdf


def _media(pdf):
    return {"id":6,"file_path":str(pdf),"title":"The memories of Mervyn Neil Knuckey","exists_on_disk":1}


def test_release_identity_is_multi_page_qa_pass_1():
    source=Path("macos_app/build_app.py").read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.10 — Multi-page PDF Reproduction QA Pass 1"' in source


def test_two_equal_a4_pages_use_identical_maximum_fit_class(tmp_path):
    html=pub._fitted_document_block(
        _media(_two_page_pdf(tmp_path)),tmp_path/"book.html","Other Documents",
        person_name="Mervyn Neil Knuckey",db=None,
    )
    assert html.count("document-source-page portrait")==2
    assert html.count("document-source-preview")==2
    assert "archive-page portrait pdf-extra-page" not in html
    assert "document-fitted-page portrait" not in html
    assert html.index("_page_001.png") < html.index("_page_002.png")


def test_multi_page_geometry_maximises_a4_printable_area():
    css=pub.PRO_CSS
    assert ".document-source-page" in css
    assert "max-width:180mm" in css
    assert "max-height:244mm" in css
    assert "object-fit:contain" in css
    assert ".document-source-page.landscape .document-source-preview" in css
    assert "max-width:244mm; max-height:180mm" in css
    assert ".document-source-page { display:block !important; }" in css


def test_single_page_birth_certificate_keeps_existing_birth_layout(tmp_path):
    fitz=pytest.importorskip("pymupdf")
    pdf=tmp_path/"Birth Certificate.pdf"
    doc=fitz.open(); doc.new_page(width=595,height=842); doc.save(pdf); doc.close()
    m={"id":1,"file_path":str(pdf),"title":"Birth Certificate","exists_on_disk":1}
    html=pub._birth_document_block(m,tmp_path/"birth.html",person_name="Mervyn Neil Knuckey",db=None)
    assert html.count("birth-document-page portrait")==1
    assert "document-source-page" not in html


def test_photo_page_contract_remains_frozen():
    css=pub.PRO_CSS
    assert "grid-template-rows:113mm 113mm" in css
    assert "transform:translateY(8mm)" in css
    assert "max-height:106mm !important" in css
    assert "max-height:91mm !important" in css
