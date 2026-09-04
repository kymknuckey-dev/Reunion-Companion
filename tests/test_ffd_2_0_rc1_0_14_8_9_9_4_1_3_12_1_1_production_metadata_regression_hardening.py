from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

def live_release(path):
    source = path.read_text()
    matches = re.findall(r'^APP_RELEASE="([^"]+)"', source, re.MULTILINE)
    assert matches, f"No live APP_RELEASE found in {path}"
    return matches[-1]

def test_current_release_identity_and_packaging_metadata_are_in_sync():
    build = live_release(ROOT / "macos_app/build_app.py")
    dmg = live_release(ROOT / "macos_app/package_dmg.py")
    assert build == dmg
    assert build.startswith("FFD 2.0 RC1.0.")
    assert " — " in build
