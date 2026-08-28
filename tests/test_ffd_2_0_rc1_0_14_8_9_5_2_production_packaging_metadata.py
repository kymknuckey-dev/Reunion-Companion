from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
EXPECTED="FFD 2.0 RC1.0.14.8.9.5.2 — Production Packaging Metadata Sync"

def live_release(path):
    text=path.read_text()
    matches=re.findall(r'^APP_RELEASE="([^"]+)"$',text,re.MULTILINE)
    assert len(matches)==1
    return matches[0]

def test_production_build_and_dmg_release_metadata_are_current_and_in_sync():
    build=live_release(ROOT/"macos_app/build_app.py")
    dmg=live_release(ROOT/"macos_app/package_dmg.py")
    assert build == EXPECTED
    assert dmg == EXPECTED
    assert build == dmg

def test_dmg_packager_builds_fresh_app_from_build_script():
    text=(ROOT/"macos_app/package_dmg.py").read_text()
    assert "macos_app/build_app.py" in text
    assert "'--output'" in text
    assert "verify_dmg(plan)" in text
