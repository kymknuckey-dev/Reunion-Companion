from pathlib import Path
import importlib.util,sys
MODULE=Path(__file__).parents[1]/"macos_app"/"build_app.py"
spec=importlib.util.spec_from_file_location("b4",MODULE); m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)

def test_identity_preserves_frozen_engine():
    assert int(m.APP_BUILD)>=4
    assert m.APP_RELEASE.startswith("FFD 2.0 ")
    assert m.ENGINE_BASELINE=="FFD 1.9 RC1"

def test_launcher_uses_bundle_runtime_not_repository():
    s=m.swift_source(Path("/tmp/should-not-appear"))
    assert "Bundle.main.resourceURL" in s
    assert "Runtime/ReunionCompanionBackend/ReunionCompanionBackend" in s
    assert ".venv/bin/python" not in s
    assert "PYTHONPATH" not in s
    assert "/tmp/should-not-appear" not in s

def test_diagnostics_exposes_runtime_location():
    s=m.swift_source(Path("/tmp/x"))
    assert "Runtime: \\(runtimePath)" in s
    assert r"Runtime: \(runtimePath)" in s

def test_builder_freezes_backend_and_dependencies():
    src=MODULE.read_text()
    assert '"-m","PyInstaller"' in src
    assert '"--onedir"' in src
    assert '"--collect-all","PIL"' in src
    assert '"--collect-all","pymupdf"' in src
    assert 'from reunion_companion.companion.ui import main' in src

def test_build_validation_requires_freezer():
    src=MODULE.read_text()
    assert "PyInstaller is required to build the self-contained runtime" in src

def test_user_data_remains_external():
    s=m.swift_source(Path("/tmp/x"))
    assert '.reunion-companion/companion.sqlite3' in s
    assert 'Library/Logs/Reunion Companion/backend.log' in s

def test_shell_identity():
    from reunion_companion import app_identity
    assert app_identity.APP_SERIES=="2.0"
    assert int(app_identity.APP_BUILD)>=4
    assert app_identity.ENGINE_BASELINE=="FFD 1.9 RC1"
