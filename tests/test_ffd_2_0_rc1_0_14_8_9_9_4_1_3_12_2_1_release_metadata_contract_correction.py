from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = 'FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.2.1 — Release Metadata Contract Correction'

def live_release(path):
    source = path.read_text()
    matches = re.findall(r'^APP_RELEASE="([^"]+)"', source, re.MULTILINE)
    assert matches, f"No live APP_RELEASE found in {path}"
    return matches[-1]

def test_release_metadata_contract_remains_forward_compatible():
    build_path = ROOT / "macos_app/build_app.py"
    dmg_path = ROOT / "macos_app/package_dmg.py"
    build = live_release(build_path)
    dmg = live_release(dmg_path)
    assert build == dmg
    assert build.startswith("FFD 2.0 RC1.0.")
    assert " — " in build
    # Preserve the historical release identity without freezing the live release forever.
    assert HISTORICAL in build_path.read_text()
    assert HISTORICAL in dmg_path.read_text()
