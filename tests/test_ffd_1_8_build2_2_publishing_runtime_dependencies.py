from pathlib import Path


def test_publishing_runtime_dependencies_are_declared():
    text = Path('pyproject.toml').read_text(encoding='utf-8').casefold()
    assert 'pillow' in text
    assert 'pymupdf' in text


def test_pdf_image_runtime_imports():
    from PIL import Image
    import pymupdf
    assert Image is not None
    assert pymupdf is not None


def test_family_book_pdf_preview_renders_all_pages(tmp_path):
    import pymupdf
    from reunion_companion.companion.document_renderer import render_pdf

    pdf = tmp_path / 'family-book.pdf'
    doc = pymupdf.open()
    for label in ('Family Book page one', 'Family Book page two'):
        page = doc.new_page()
        page.insert_text((72, 72), label)
    doc.save(pdf)
    doc.close()

    output_html = tmp_path / 'family-book.html'
    result = render_pdf(pdf, output_html, 'family-book')
    assert result['renderer'] == 'PyMuPDF'
    assert len(result['pages']) == 2
    for page in result['pages']:
        assert Path(page['preview']).exists()
        assert Path(page['preview']).stat().st_size > 0


def test_portability_bootstrap_checks_publishing_runtime():
    text = Path('tools/bootstrap_portable_mac.py').read_text(encoding='utf-8')
    assert 'Pillow' in text
    assert 'PyMuPDF' in text
