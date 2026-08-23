from pathlib import Path

import pytest

from reunion_companion.companion.document_renderer import render_pdf
from reunion_companion.companion import publishing_v11 as pub


def _two_page_pdf(tmp_path):
    fitz=pytest.importorskip("pymupdf")
    pdf=tmp_path/"The memories of Mervyn Neil Knuckey.pdf"
    doc=fitz.open()
    p1=doc.new_page(width=595,height=842)
    p1.insert_text((72,100),"The memories of Mervyn Neil Knuckey — page 1")
    p2=doc.new_page(width=595,height=842)
    p2.insert_text((72,100),"The memories of Mervyn Neil Knuckey — page 2")
    doc.save(pdf)
    doc.close()
    return pdf


def _one_page_pdf(tmp_path,name):
    fitz=pytest.importorskip("pymupdf")
    pdf=tmp_path/name
    doc=fitz.open()
    page=doc.new_page(width=595,height=842)
    page.insert_text((72,100),name)
    doc.save(pdf)
    doc.close()
    return pdf


def _media(pdf,mid=6,title="The memories of Mervyn Neil Knuckey"):
    return {"id":mid,"file_path":str(pdf),"title":title,"exists_on_disk":1}


def test_release_identity_is_rc1_0_10():
    source=Path("macos_app/build_app.py").read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.10 — Multi-page PDF Reproduction"' in source


def test_renderer_requires_and_reports_complete_two_page_render(tmp_path):
    pdf=_two_page_pdf(tmp_path)
    result=render_pdf(pdf,tmp_path/"book.html",6,dpi=72)
    assert result["renderer"]=="PyMuPDF"
    assert result["page_count"]==2
    assert result["all_pages_rendered"] is True
    assert [p["page"] for p in result["pages"]]==[1,2]
    assert all(Path(p["preview"]).is_file() for p in result["pages"])


def test_person_other_document_prints_page_one_then_page_two(tmp_path):
    pdf=_two_page_pdf(tmp_path)
    html=pub._fitted_document_block(
        _media(pdf),tmp_path/"book.html","Other Documents",
        person_name="Mervyn Neil Knuckey",db=None,
    )
    assert html.count("document-fitted-page portrait")==1
    assert html.count("archive-page portrait pdf-extra-page")==1
    assert "_page_001.png" in html
    assert "_page_002.png" in html
    assert html.index("_page_001.png") < html.index("_page_002.png")
    assert "Page 1" in html
    assert "Page 2" in html


def test_single_page_certificate_keeps_single_fitted_page(tmp_path):
    pdf=_one_page_pdf(tmp_path,"Knuckey, Mervyn Neil 1933-09-24 Birth Certificate.pdf")
    html=pub._birth_document_block(
        _media(pdf,1,"Knuckey, Mervyn Neil 1933-09-24 Birth Certificate"),
        tmp_path/"birth.html",person_name="Mervyn Neil Knuckey",db=None,
    )
    assert html.count("birth-document-page portrait")==1
    assert "pdf-extra-page" not in html


def test_rc1_0_9_photo_page_contract_is_unchanged():
    css=pub.PRO_CSS
    assert "grid-template-rows:113mm 113mm" in css
    assert "transform:translateY(8mm)" in css
    assert "max-height:106mm !important" in css
    assert "max-height:91mm !important" in css
    assert "object-fit:contain !important" in css
