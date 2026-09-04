from datetime import datetime, timedelta, timezone
from pathlib import Path

from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence import ensure_external_evidence
from reunion_companion.companion.external_research_runner import runner_status
from reunion_companion.companion import beta_ui

NOW=datetime(2026,9,4,3,30,0,tzinfo=timezone.utc)


def test_runner_status_exposes_actual_next_retry_after_source_cooldown(tmp_path):
    db=connect(tmp_path/'retry.sqlite3')
    ensure_external_evidence(db)
    db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('ryerson_runner_enabled','1')")
    row_retry=NOW+timedelta(minutes=10)
    cooldown=NOW+timedelta(minutes=25)
    db.execute(
        "INSERT INTO companion_external_scan_queue(source_name,person_gedcom_xref,status,next_retry_at) VALUES(?,?,?,?)",
        ('Ryerson','@I1@','retry_wait',row_retry.isoformat()),
    )
    db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('ryerson_runner_cooldown_until',?)",(cooldown.isoformat(),))
    db.commit()
    status=runner_status(db)
    assert status['retry_wait']==1
    assert status['next_retry_at']==cooldown.isoformat()


def test_retry_status_formats_clock_and_relative_wait():
    run={'retry_wait':1,'next_retry_at':(NOW+timedelta(minutes=25)).isoformat()}
    text=beta_ui._ryerson_retry_status(run,now=NOW)
    assert text.startswith('Next retry: ')
    assert '· in 25 min' in text


def test_retry_status_reports_none_when_no_retry_is_pending():
    assert beta_ui._ryerson_retry_status({'retry_wait':0,'next_retry_at':None},now=NOW)=='Next retry: None pending'


def test_release_identity_ryerson_retry_timing_visibility():
    expected='FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.2 — Ryerson Retry Timing Visibility'
    assert f'APP_RELEASE="{expected}"' in Path('macos_app/build_app.py').read_text()
    assert f'APP_RELEASE="{expected}"' in Path('macos_app/package_dmg.py').read_text()
