from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_family_switch_skips_external_reconciliation_and_pauses_runner():
    ui=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    assert 'pause_for_family_change(db)' in ui
    assert 'staged_import(db_path,path,reconcile_external=False)' in ui

def test_safe_refresh_supports_switch_without_external_reconciliation():
    src=(ROOT/'src/reunion_companion/companion/safe_refresh.py').read_text()
    assert 'reconcile_external: bool = True' in src
    assert '"skipped": "family_file_switch"' in src

def test_runner_has_family_owner_and_mismatch_guard():
    src=(ROOT/'src/reunion_companion/companion/external_research_runner.py').read_text()
    assert 'META_OWNER_WORKSPACE="ryerson_runner_owner_workspace_id"' in src
    assert 'runner_matches_active_family(db)' in src
    assert 'paused_family_mismatch' in src
    assert 'Queue Family File:' in (ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()

def test_native_gedcom_picker_accepts_ged_and_gedcom_extensions():
    src=(ROOT/'macos_app/build_app.py').read_text()
    assert src.count('panel.allowedFileTypes=["ged","gedcom"]') >= 2

def test_release_identity_advanced():
    expected='FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.10.4.1 — Family Context Safety & GEDCOM Locate QA'
    assert f'APP_RELEASE="{expected}"' in (ROOT/'macos_app/build_app.py').read_text()
    assert f'APP_RELEASE="{expected}"' in (ROOT/'macos_app/package_dmg.py').read_text()
