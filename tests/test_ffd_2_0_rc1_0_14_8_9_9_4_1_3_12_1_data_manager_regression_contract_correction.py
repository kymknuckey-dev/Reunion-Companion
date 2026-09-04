from pathlib import Path


def test_release_identity_data_manager_regression_contract_correction():
    source=Path("macos_app/build_app.py").read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.1 — Data Manager Regression Contract Correction"' in source
    dmg=Path("macos_app/package_dmg.py").read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.1 — Data Manager Regression Contract Correction"' in dmg
