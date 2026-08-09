from pathlib import Path
import pytest
from reunion_companion.companion.publishing_v11 import _pdf_block,PRO_CSS,_caption,_clean_document_title

def make_pdf(tmp_path):
    fitz=pytest.importorskip("fitz")
    p=tmp_path/"Example Landscape Marriage Certificate.pdf"
    doc=fitz.open()
    pg=doc.new_page(width=842,height=595)
    pg.insert_text((72,100),"Landscape certificate")
    doc.save(p);doc.close()
    return p

def test_pdf_web_preview_is_single_natural_orientation(tmp_path):
    p=make_pdf(tmp_path)
    m={"id":5,"file_path":str(p),"title":"Example Landscape Marriage Certificate","exists_on_disk":1}
    html=_pdf_block(m,tmp_path/"book.html",family_names="Example Couple")
    # One web plate.
    assert html.count("pdf-web-plate") == 1
    # Print archive page is present in DOM but CSS-hidden on screen.
    assert "archive-page landscape" in html
    assert ".archive-page {" in PRO_CSS and "display:none;" in PRO_CSS
    # Landscape rotation is print-only CSS.
    assert "rotate(90deg)" in PRO_CSS
    assert "@media print" in PRO_CSS
    assert ".archive-page { display:block !important; }" in PRO_CSS

def test_document_caption_is_reader_friendly():
    m={"title":"Knuckey, Mervyn Neil 1933-09-24 Birth Certificate.pdf"}
    # Role recognition is deterministic from supplied title.
    assert _clean_document_title(m["title"],"Mervyn Neil Knuckey",None)=="Birth Certificate"
    c=_caption(m,"Mervyn Neil Knuckey",None,1)
    assert "Birth Certificate" in c
    assert "Mervyn Neil Knuckey" in c
    assert "Page 1" in c

def test_life_topic_css_present():
    assert ".life-topic" in PRO_CSS
    assert "max-height:82vh" in PRO_CSS
