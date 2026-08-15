from pathlib import Path
import importlib.util,sys
MODULE=Path(__file__).parents[1]/"macos_app"/"build_app.py"
spec=importlib.util.spec_from_file_location("b5",MODULE); m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)

def test_identity_preserves_frozen_engine():
    assert m.APP_BUILD=="5"
    assert m.APP_RELEASE=="FFD 2.0 Build 5 — Installation & First-Run Experience"
    assert m.ENGINE_BASELINE=="FFD 1.9 RC1"

def test_first_run_is_native_and_only_needed_without_genealogy_data():
    s=m.swift_source(Path("/tmp/x"))
    assert "/setup/status" in s
    assert "needs_genealogy_data" in s
    assert "Welcome to Reunion Companion" in s
    assert "No family history has been loaded yet." in s
    assert "Import GEDCOM…" in s
    assert "Continue" in s
    assert "ollamaModelStatus()" in s
    assert "AI model available" in s

def test_first_run_uses_native_gedcom_file_chooser_and_backend_import():
    s=m.swift_source(Path("/tmp/x"))
    assert "NSOpenPanel" in s
    assert 'filenameExtension:"ged"' in s
    assert 'filenameExtension:"gedcom"' in s
    assert "/setup/import" in s
    assert "URLQueryItem(name:\"path\",value:file.path)" in s

def test_existing_user_skips_setup_and_build4_runtime_is_preserved():
    s=m.swift_source(Path("/tmp/x"))
    assert "if setupRequired() { showFirstRun() } else { loadCompanion() }" in s
    assert "Runtime/ReunionCompanionBackend/ReunionCompanionBackend" in s
    assert ".venv/bin/python" not in s

def test_first_run_backend_contract_exists():
    src=(MODULE.parents[1]/"src/reunion_companion/companion/beta_ui.py").read_text()
    assert 'u.path=="/setup/status"' in src
    assert '"needs_genealogy_data":people==0' in src
    assert 'u.path=="/setup/import"' in src
    assert "safe_refresh(db_path,incoming)" in src
    assert 'record_workspace_import(db,ff["id"],incoming)' in src

def test_install_cleans_duplicate_discoverable_dist_app():
    src=MODULE.read_text()
    assert "Cleaned build artifact" in src
    assert "shutil.rmtree(app)" in src

def test_diagnostics_and_shell_identity():
    s=m.swift_source(Path("/tmp/x"))
    assert "FFD 2.0 Build 5 — Installation & First-Run Experience" in s
    assert "Runtime: \\(runtimePath)" in s
    from reunion_companion import app_identity
    assert app_identity.APP_DISPLAY=="FFD 2.0 Build 5"
    assert app_identity.APP_RELEASE_NAME=="Installation & First-Run Experience"
    assert app_identity.ENGINE_BASELINE=="FFD 1.9 RC1"
