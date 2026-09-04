from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = 'FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.1.1 — Production Metadata Regression Hardening'

def live_release(path):
    source = path.read_text()
    matches = re.findall(r'^APP_RELEASE="([^"]+)"', source, re.MULTILINE)
    assert matches
    return matches[-1]

def test_current_release_identity_and_packaging_metadata_are_in_sync():
    assert live_release(ROOT / "macos_app/build_app.py") == EXPECTED
    assert live_release(ROOT / "macos_app/package_dmg.py") == EXPECTED
