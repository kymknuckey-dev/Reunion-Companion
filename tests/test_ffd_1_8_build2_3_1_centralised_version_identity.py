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


def test_release_identity_is_build_2_3_1():
    assert FFD_SERIES == "1.8"
    assert FFD_BUILD == "2.3.1"
    assert RELEASE_NAME == "Centralised Version Identity"
    assert RELEASE_TAG == "ffd-1.8-build-2.3.1"
    assert FFD_DISPLAY == "FFD 1.8 Build 2.3.1"
    assert APP_DISPLAY_NAME == "Reunion Companion — FFD 1.8 Build 2.3.1 Centralised Version Identity"


def test_ui_header_uses_central_release_identity():
    html = layout("Version test", "<p>ok</p>")
    assert "FFD 1.8 Build 2.3.1" in html
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
