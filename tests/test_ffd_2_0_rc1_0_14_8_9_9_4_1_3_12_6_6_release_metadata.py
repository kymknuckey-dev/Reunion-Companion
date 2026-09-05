from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_release_metadata():
    expected='FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.6.6 — External Evidence Identity & Review Lifecycle Correction'
    assert f'APP_RELEASE="{expected}"' in (ROOT/'macos_app/build_app.py').read_text()
    assert f'APP_RELEASE="{expected}"' in (ROOT/'macos_app/package_dmg.py').read_text()
