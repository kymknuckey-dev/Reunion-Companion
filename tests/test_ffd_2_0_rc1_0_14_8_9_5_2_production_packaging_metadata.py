import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPECTED="FFD 2.0 RC1.0.14.8.9.8.1 — Manage Presentation QA Correction"


def live_release(path):
    text=path.read_text()
    match=re.search(r'^APP_RELEASE="([^"]+)"',text,re.MULTILINE)
    assert match, f"No live APP_RELEASE found in {path}"
    return match.group(1)


def test_production_build_and_dmg_release_metadata_are_current_and_in_sync():
    build=live_release(ROOT/"macos_app/build_app.py")
    dmg=live_release(ROOT/"macos_app/package_dmg.py")
    assert build == EXPECTED
    assert dmg == EXPECTED
