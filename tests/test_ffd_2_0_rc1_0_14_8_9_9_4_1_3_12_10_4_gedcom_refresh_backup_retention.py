from pathlib import Path
import sqlite3

from reunion_companion.companion.safe_refresh import (
    AUTO_REFRESH_BACKUP_RETENTION,
    backup_housekeeping_status,
    cleanup_refresh_housekeeping,
    prune_refresh_backups,
)


def _file(path: Path, size: int=16):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'x' * size)


def test_refresh_backup_retention_is_three(tmp_path):
    db=tmp_path/'companion.sqlite3'; _file(db)
    for i in range(6):
        p=tmp_path/'backups'/f'companion-before-refresh-20260908-120{i}00.sqlite3'
        _file(p, 10+i)
        p.touch()
    assert AUTO_REFRESH_BACKUP_RETENTION == 3
    removed=prune_refresh_backups(db)
    assert len(removed)==3
    assert len(list((tmp_path/'backups').glob('companion-before-refresh-*.sqlite3')))==3


def test_cleanup_preserves_ryerson_checkpoint_but_removes_bickle_and_stale_stage(tmp_path):
    db=tmp_path/'companion.sqlite3'; _file(db)
    for i in range(5): _file(tmp_path/'backups'/f'companion-before-refresh-20260908-12{i:02d}00.sqlite3')
    ryerson=tmp_path/'companion-before-ryerson-reset.sqlite3'; _file(ryerson)
    bickle=tmp_path/'companion.sqlite3.before-bickle-cleanup'; _file(bickle)
    stage=tmp_path/'reunion-companion-refresh-old.sqlite3'; _file(stage)
    result=cleanup_refresh_housekeeping(db)
    assert result['removed_count']==4
    assert ryerson.exists()
    assert not bickle.exists()
    assert not stage.exists()
    assert backup_housekeeping_status(db)['count']==3


def test_manage_source_uses_expected_gedcom_and_contextual_locator():
    text=Path('src/reunion_companion/companion/beta_ui.py').read_text()
    assert 'EXPECTED GEDCOM' in text
    assert 'Safe Refresh reloads the GEDCOM associated with the active Family File.' in text
    assert 'Choose Different GEDCOM' not in text
    assert 'Locate GEDCOM…' in text
    swift=Path('macos_app/build_app.py').read_text()
    assert 'func locateGEDCOM()' in swift
    assert 'url.host=="locate-gedcom"' in swift
