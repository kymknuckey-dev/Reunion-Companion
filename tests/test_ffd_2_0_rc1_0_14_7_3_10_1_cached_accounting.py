from datetime import datetime, timezone

from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_surname_bootstrap import (
    _progress_can_finalize_locally,
    bootstrap_status,
    run_one_surname,
)

NOW=datetime(2026,8,26,0,0,0,tzinfo=timezone.utc)


def _richards_fixture(db):
    db.execute(
        """
        INSERT INTO companion_ryerson_surname_queue(
            surname,surname_key,people_count,status,attempts,result_count
        ) VALUES('Richards','richards',10,'queued',14,1996)
        """
    )

    db.execute(
        """
        INSERT INTO companion_ryerson_surname_progress(
            surname_key,surname,current_page,current_url,pages_completed,
            rows_seen,inserted_rows,existing_rows,is_complete
        ) VALUES(
            'richards','Richards',2,
            'https://ryersonindex.org/search.php?page=2',
            2,2000,1996,4,0
        )
        """
    )

    for i in range(1996):
        db.execute(
            """
            INSERT INTO companion_external_notice_cache(
                source_name,record_key,harvest_kind,harvest_value,
                harvest_year,normalized_json
            ) VALUES('Ryerson',?,'surname','Richards',2026,'{}')
            """,
            (f'richards-{i}',),
        )

    db.commit()


def test_richards_accounting_can_finalize_locally(tmp_path):
    db=connect(tmp_path/"x.db")
    try:
        _richards_fixture(db)
        assert _progress_can_finalize_locally(db,"Richards") is True
    finally:
        db.close()


def test_local_finalisation_does_not_reenter_harvest(tmp_path, monkeypatch):
    db=connect(tmp_path/"x.db")
    try:
        _richards_fixture(db)

        monkeypatch.setattr(
            "reunion_companion.companion.ryerson_surname_bootstrap.cross_match_surname",
            lambda db,surname: {"findings":0},
        )

        calls=[]
        def harvest(db,surname):
            calls.append(surname)
            raise AssertionError("Safari harvest must not run")

        result=run_one_surname(db,now=NOW,harvest_fn=harvest)

        assert result["status"]=="completed"
        assert result["finalized_locally"] is True
        assert calls==[]

        q=db.execute(
            "SELECT status,result_count FROM companion_ryerson_surname_queue "
            "WHERE surname_key='richards'"
        ).fetchone()
        assert q["status"]=="completed"
        assert q["result_count"]==1996

        p=db.execute(
            "SELECT rows_seen,inserted_rows,existing_rows,is_complete "
            "FROM companion_ryerson_surname_progress "
            "WHERE surname_key='richards'"
        ).fetchone()
        assert p["rows_seen"]==2000
        assert p["inserted_rows"]==1996
        assert p["existing_rows"]==4
        assert p["is_complete"]==1
    finally:
        db.close()


def test_expired_global_cooldown_not_reported_as_active(tmp_path):
    db=connect(tmp_path/"x.db")
    try:
        db.execute(
            "INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",
            ("ryerson_surname_bootstrap_cooldown_until",
             "2020-01-01T00:00:00+00:00"),
        )
        db.commit()

        status=bootstrap_status(db)
        assert status["source_waiting"] is False
        assert status["cooldown_until"]=="2020-01-01T00:00:00+00:00"
    finally:
        db.close()
