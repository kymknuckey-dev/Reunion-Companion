from pathlib import Path
import importlib.util,sys
ROOT=Path(__file__).parents[1]
MODULE=ROOT/'macos_app/package_dmg.py'
spec=importlib.util.spec_from_file_location('b6',MODULE); m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)

def test_identity_and_engine_baseline():
    assert m.APP_BUILD=='6'
    assert m.APP_RELEASE.startswith('FFD 2.0 ')
    assert m.ENGINE_BASELINE=='FFD 1.9 RC1'

def test_distribution_contract():
    src=MODULE.read_text()
    assert "release_dir or repo/'dist'/'release'" in src
    assert "DMG_NAME=\"Reunion Companion.dmg\"" in src
    assert "(stage/'Applications').symlink_to('/Applications')" in src
    assert "'-format','UDZO'" in src
    assert "hdiutil,'verify'" in src
    assert "hdiutil,'attach','-readonly','-nobrowse'" in src
    assert "hdiutil,'detach'" in src

def test_package_uses_temporary_app_not_repo_dist_app():
    src=MODULE.read_text()
    assert "TemporaryDirectory(prefix='reunion-companion-dmg-')" in src
    assert "'--output',str(app)" in src
    assert "repo/'dist'/'Reunion Companion.app'" not in src

def test_distribution_verifies_embedded_runtime():
    src=MODULE.read_text()
    assert "Contents/Resources/Runtime/ReunionCompanionBackend/ReunionCompanionBackend" in src

def test_signing_is_deliberately_deferred():
    src=MODULE.read_text()
    assert 'Signing: not part of Build 6' in src
    assert 'Notarisation: not part of Build 6' in src

def test_shell_identity():
    from reunion_companion import app_identity
    assert app_identity.APP_DISPLAY.startswith('FFD 2.0 ')
    assert app_identity.APP_RELEASE_NAME
    assert app_identity.ENGINE_BASELINE=='FFD 1.9 RC1'
