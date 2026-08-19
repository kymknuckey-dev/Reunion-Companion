from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_rc108_release_identity():
    source=(ROOT/'macos_app'/'build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.9 — Media Semantics & Book Presentation Pass 6"' in source


def test_frozen_backend_eagerly_initialises_utf16le_and_weasyprint():
    source=(ROOT/'macos_app'/'build_app.py').read_text()
    assert "codecs.lookup('utf-16le')" in source
    assert "'Reunion Companion'.encode('utf-16le')" in source
    assert 'from weasyprint import HTML as _FrozenWeasyHTML' in source
    # Eager import must occur before normal Companion server startup.
    assert source.index("from weasyprint import HTML as _FrozenWeasyHTML") < source.index('from reunion_companion.companion.ui import main\\n')


def test_frozen_pdf_probe_uses_preloaded_runtime_and_representative_html():
    source=(ROOT/'macos_app'/'build_app.py').read_text()
    assert "_FrozenWeasyHTML(string=" in source
    assert 'representative typography test' in source
    assert 'Frozen PDF runtime OK' in source


def test_pdf_import_failure_logs_full_traceback_before_friendly_error():
    source=(ROOT/'src'/'reunion_companion'/'companion'/'publishing_v11.py').read_text()
    assert 'import traceback' in source
    assert 'traceback.print_exc()' in source
    assert 'PDF publishing runtime could not be loaded' in source
