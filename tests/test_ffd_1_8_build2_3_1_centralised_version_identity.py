from pathlib import Path

from reunion_companion.companion.beta_ui import layout
from reunion_companion.companion.version_identity import (
    APP_DISPLAY_NAME,
    FFD_BUILD,
    FFD_DISPLAY,
    FFD_SERIES,
    RELEASE_NAME,
    RELEASE_TAG,
    release_identity,
)


def test_release_identity_is_centralised():
    assert FFD_SERIES
    assert FFD_BUILD
    assert RELEASE_NAME
    assert RELEASE_TAG.startswith(f"ffd-{FFD_SERIES}-")
    assert FFD_DISPLAY.startswith(f"FFD {FFD_SERIES} ")
    assert APP_DISPLAY_NAME == f"Reunion Companion — {FFD_DISPLAY} {RELEASE_NAME}"


def test_ui_header_uses_central_release_identity():
    html = layout("Version test", "<p>ok</p>")
    assert FFD_DISPLAY in html
    assert "FFD 1.8 Build 2.1.2" not in html


def test_beta_ui_has_no_stale_hard_coded_release_identity():
    src = Path(__file__).parents[1] / "src/reunion_companion/companion/beta_ui.py"
    text = src.read_text(encoding="utf-8")
    assert "FFD 1.8 Build 2.1.2" not in text
    assert "Reunion Companion — FFD 1.8 Build 2.1 Family File Management & Import Safety UX" not in text
    assert "from .version_identity import APP_DISPLAY_NAME, FFD_DISPLAY" in text
    assert "print(APP_DISPLAY_NAME)" in text


def test_release_identity_dictionary_is_consistent():
    ident = release_identity()
    assert ident["tag"] == RELEASE_TAG
    assert ident["display"] == FFD_DISPLAY
    assert ident["application"] == APP_DISPLAY_NAME
