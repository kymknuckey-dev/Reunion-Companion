from pathlib import Path
import sqlite3
import pytest
from reunion_companion.companion.publishing_v11 import (
    source_label,_pdf_block,export_pdf_from_html,PRO_CSS
)
from reunion_companion.companion.document_renderer import render_pdf

def _pdf(tmp_path):
    fitz=pytest.importorskip("fitz")
    p=tmp_path/"mixed orientation.pdf"
    doc=fitz.open()
    a=doc.new_page(width=595,height=842)
    a.insert_text((72,100),"Portrait page")
    b=doc.new_page(width=842,height=595)
    b.insert_text((72,100),"Landscape page")
    doc.save(p)
    doc.close()
    return p

def test_pdf_renderer_all_pages_and_orientation(tmp_path):
    p=_pdf(tmp_path)
    html=tmp_path/"book.html"
    r=render_pdf(p,html,77,dpi=72)
    assert len(r["pages"])==2
    assert r["pages"][0]["orientation"]=="portrait"
    assert r["pages"][1]["orientation"]=="landscape"
    assert (tmp_path/"book_assets").exists()

def test_web_preview_and_print_archive_rules(tmp_path):
    p=_pdf(tmp_path)
    m={"id":77,"file_path":str(p),"title":"Marriage Certificate","exists_on_disk":1}
    html=_pdf_block(m,tmp_path/"book.html",family_names="Example Couple")
    assert "Open original PDF" not in html
    assert "web-only" in html
    assert "document-source-page portrait" in html
    assert "document-source-page landscape" in html
    assert "document-source-preview" in html
    assert "rotate(90deg)" in PRO_CSS

def test_publication_source_label_removes_gedcom_at_signs():
    s={"gedcom_xref":"@S17@","id":17}
    assert source_label(s)=="[17]"
    assert "@" not in source_label(s)

def test_direct_pdf_export(tmp_path):
    pytest.importorskip("weasyprint")
    h=tmp_path/"simple.html"
    h.write_text("<html><body><h1>Hello</h1></body></html>")
    p=export_pdf_from_html(h,tmp_path/"simple.pdf")
    assert p.exists() and p.stat().st_size>100
