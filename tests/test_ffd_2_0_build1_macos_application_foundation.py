from pathlib import Path
import importlib.util, sys

MODULE=Path(__file__).parents[1]/"macos_app"/"build_app.py"
spec=importlib.util.spec_from_file_location("rc_macos_foundation_contract",MODULE)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

def test_application_foundation_preserves_frozen_engine():
    # Build 1 established this boundary. Later 2.0 builds may advance the shell.
    assert m.APP_VERSION=="2.0"
    assert m.ENGINE_BASELINE=="FFD 1.9 RC1"

def test_app_builder_still_targets_native_macos_bundle(tmp_path):
    plan=m.make_plan(repo=Path(__file__).parents[1],output=tmp_path/"Reunion Companion.app")
    assert plan.output.name=="Reunion Companion.app"
    plist=m.info_plist()
    assert plist["CFBundlePackageType"]=="APPL"
    assert plist["CFBundleIdentifier"]=="com.reunioncompanion.app"
    assert plist["CFBundleShortVersionString"]=="2.0"
    assert int(plist["CFBundleVersion"]) >= 1

def test_launcher_preserves_hidden_backend_lifecycle_contract():
    src=m.swift_source(Path("/tmp/Reunion Companion"))
    assert "Process()" in src
    assert ".venv/bin/python" in src or "Runtime/ReunionCompanionBackend" in src
    assert "--no-browser" in src
    assert "applicationWillTerminate" in src
    assert "p.terminate()" in src

def test_launcher_preserves_readiness_and_diagnostics_contract():
    src=m.swift_source(Path("/tmp/Reunion Companion"))
    assert "isCompanionReady()" in src
    assert 'localizedCaseInsensitiveContains("Reunion Companion")' in src
    assert "backend.log" in src
    assert "About Reunion Companion" in src

def test_shell_identity_keeps_engine_identity_distinct():
    from reunion_companion import app_identity
    assert app_identity.APP_SERIES=="2.0"
    assert int(app_identity.APP_BUILD) >= 1
    assert app_identity.ENGINE_BASELINE=="FFD 1.9 RC1"
