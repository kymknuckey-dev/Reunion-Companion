from pathlib import Path
import importlib.util, sys

MODULE=Path(__file__).parents[1]/"macos_app"/"build_app.py"
spec=importlib.util.spec_from_file_location("rc_macos_builder",MODULE)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

def test_application_identity_is_separate_from_frozen_engine():
    assert m.APP_RELEASE=="FFD 2.0 Build 1 — macOS Application Foundation"
    assert m.ENGINE_BASELINE=="FFD 1.9 RC1"

def test_app_builder_targets_native_macos_bundle(tmp_path):
    plan=m.make_plan(repo=Path(__file__).parents[1],output=tmp_path/"Reunion Companion.app")
    assert plan.output.name=="Reunion Companion.app"
    plist=m.info_plist()
    assert plist["CFBundlePackageType"]=="APPL"
    assert plist["CFBundleIdentifier"]=="com.reunioncompanion.app"
    assert plist["CFBundleShortVersionString"]=="2.0"
    assert plist["CFBundleVersion"]=="1"

def test_launcher_owns_service_lifecycle_and_hides_terminal():
    src=m.swift_source(Path("/tmp/Reunion Companion"))
    assert "Process()" in src
    assert ".venv/bin/python" in src
    assert '["-m","reunion_companion.companion.ui","--no-browser"]' in src
    assert "NSWorkspace.shared.open(companionURL)" in src
    assert "applicationWillTerminate" in src
    assert "p.terminate()" in src

def test_launcher_has_readiness_duplicate_and_diagnostic_contract():
    src=m.swift_source(Path("/tmp/Reunion Companion"))
    assert "isCompanionReady()" in src
    assert 'localizedCaseInsensitiveContains("Reunion Companion")' in src
    assert "backend.log" in src
    assert "About Reunion Companion" in src
    assert "FFD 1.9 RC1" in src

def test_shell_identity_file_keeps_engine_identity_distinct():
    from reunion_companion import app_identity
    assert app_identity.APP_DISPLAY=="FFD 2.0 Build 1"
    assert app_identity.ENGINE_BASELINE=="FFD 1.9 RC1"
