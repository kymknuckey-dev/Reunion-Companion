from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence_matcher import (
    missing_death_candidates,
    ryerson_death_candidates,
)
from reunion_companion.companion.external_evidence_scan import (
    enqueue_death_research_candidates,
    queue_rows,
)
from reunion_companion.companion.beta_ui import research_page


def person(db,pid,xref,given,surname,display=None):
    db.execute(
        "INSERT INTO people("
        "id,gedcom_xref,reunion_person_id,given_names,surname,"
        "display_name,sex,raw_name"
        ") VALUES(?,?,?,?,?,?,?,?)",
        (
            pid,
            xref,
            pid,
            given,
            surname,
            display or " ".join(x for x in (given,surname) if x),
            "M",
            f"{given or ''} /{surname or ''}/",
        ),
    )


def event(db,pid,kind,date=None,place=None,note=None):
    db.execute(
        "INSERT INTO events("
        "person_id,event_type,date_text,place_text,note_text"
        ") VALUES(?,?,?,?,?)",
        (pid,kind,date,place,note),
    )


def test_broad_missing_death_still_includes_surnameless(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Ada",None,"Ada")
    db.commit()

    assert [
        r["display_name"]
        for r in missing_death_candidates(db)
    ] == ["Ada"]


def test_ryerson_requires_surname_and_birth_date(tmp_path):
    db=connect(tmp_path/"x.db")

    person(db,1,"@I1@","Ada",None,"Ada")
    event(db,1,"Birth","01 JAN 1950")

    person(db,2,"@I2@","John","Knuckey","John Knuckey")

    person(db,3,"@I3@","Peter","Rigg","Peter Rigg")
    event(db,3,"Birth","21 MAY 1944")

    db.commit()

    assert [
        r["display_name"]
        for r in ryerson_death_candidates(db)
    ] == ["Peter Rigg"]


def test_surname_without_birth_date_is_not_eligible(tmp_path):
    db=connect(tmp_path/"x.db")

    person(db,1,"@I1@","John","Knuckey","John Knuckey")
    db.commit()

    assert ryerson_death_candidates(db) == []


def test_birth_over_100_year_window_is_not_eligible(tmp_path):
    db=connect(tmp_path/"x.db")

    person(db,1,"@I1@","John","Knuckey","John Knuckey")
    event(db,1,"Birth","01 JAN 1900")

    db.commit()

    assert ryerson_death_candidates(db) == []


def test_stronger_identity_ranks_higher_among_eligible_people(tmp_path):
    db=connect(tmp_path/"x.db")

    person(db,1,"@I1@","John","Knuckey","John Knuckey")
    event(db,1,"Birth","1950")

    person(db,2,"@I2@","Peter Stanly","Rigg","Peter Stanly Rigg")
    event(
        db,
        2,
        "Birth",
        "21 MAY 1944",
        "Brighton Community Hospital",
    )
    event(
        db,
        2,
        "Death",
        None,
        None,
        "Death notice information already recorded in note",
    )

    db.commit()

    rows=ryerson_death_candidates(db)
    names=[r["display_name"] for r in rows]

    assert names.index("Peter Stanly Rigg") < names.index("John Knuckey")


def test_unattended_queue_uses_ryerson_eligibility(tmp_path):
    db=connect(tmp_path/"x.db")

    # No surname: general research only.
    person(db,1,"@I1@","Ada",None,"Ada")
    event(db,1,"Birth","1950")

    # Surname but no birth date: general research only.
    person(db,2,"@I2@","John","Knuckey","John Knuckey")

    # Surname + usable birth date within age window: Ryerson eligible.
    person(db,3,"@I3@","Peter","Rigg","Peter Rigg")
    event(db,3,"Birth","21 MAY 1944")

    db.commit()

    assert enqueue_death_research_candidates(db) == 1

    rows=queue_rows(db)

    assert len(rows) == 1
    assert rows[0]["person_gedcom_xref"] == "@I3@"


def test_research_needed_remains_broader_than_ryerson(tmp_path):
    db=connect(tmp_path/"x.db")

    # No surname and no birth date: not Ryerson eligible,
    # but still a genuine missing-death research item.
    person(db,1,"@I1@","Ada",None,"Ada")

    # Ryerson eligible.
    person(
        db,
        2,
        "@I2@",
        "Peter Stanly",
        "Rigg",
        "Peter Stanly Rigg",
    )
    event(
        db,
        2,
        "Birth",
        "21 MAY 1944",
        "Brighton Community Hospital",
    )

    db.commit()

    html=research_page(db)

    section=html.split(
        "Research Needed",1
    )[1].split(
        "Unsourced Events",1
    )[0]

    # General Research Needed deliberately contains both.
    assert "Peter Stanly Rigg" in section
    assert ">Ada<" in section

    # But only Peter is a Ryerson discovery candidate.
    assert [
        r["display_name"]
        for r in ryerson_death_candidates(db)
    ] == ["Peter Stanly Rigg"]


def test_discovery_reconciliation_retires_only_ineligible_new_people(tmp_path):
    from reunion_companion.companion.ryerson_discovery_review import (
        remember_discovery,
        reconcile_discovery_eligibility,
        set_discovery_state,
    )

    db=connect(tmp_path/"x.db")

    person(db,1,"@I1@","Eligible","Test","Eligible Test")
    event(db,1,"Birth","01 JAN 1950")

    person(db,2,"@I2@","Stale","Test","Stale Test")
    db.commit()

    keep=remember_discovery(
        db,
        person_id=1,
        source_name="Ryerson",
        external_record_key="eligible",
        proposed_fact_key="death:01JAN2020",
    )
    retire=remember_discovery(
        db,
        person_id=2,
        source_name="Ryerson",
        external_record_key="stale-new",
        proposed_fact_key="death:01JAN2020",
    )
    decided=remember_discovery(
        db,
        person_id=2,
        source_name="Ryerson",
        external_record_key="stale-decided",
        proposed_fact_key="death:01JAN2020",
    )

    set_discovery_state(db,decided["id"],"already_known")

    changed=reconcile_discovery_eligibility(db,{1})

    rows=db.execute(
        """
        SELECT external_record_key,state,decision_note
        FROM companion_external_discovery_review
        ORDER BY id
        """
    ).fetchall()

    assert changed == 1
    assert rows[0]["external_record_key"] == "eligible"
    assert rows[0]["state"] == "new"

    assert rows[1]["external_record_key"] == "stale-new"
    assert rows[1]["state"] == "ineligible"
    assert "no longer meets" in rows[1]["decision_note"].lower()

    assert rows[2]["external_record_key"] == "stale-decided"
    assert rows[2]["state"] == "already_known"


def test_discovery_reconciliation_retires_death_before_birth(tmp_path):
    from reunion_companion.companion.ryerson_discovery_review import (
        remember_discovery,
        reconcile_discovery_eligibility,
    )

    db=connect(tmp_path/"x.db")

    person(
        db,
        1,
        "@I1@",
        "David John",
        "Smith",
        "David John Smith",
    )
    event(db,1,"Birth","23 MAR 1963")
    db.commit()

    impossible=remember_discovery(
        db,
        person_id=1,
        source_name="Ryerson",
        external_record_key="ryerson:impossible",
        proposed_fact_key="death:30APR1942",
    )
    possible=remember_discovery(
        db,
        person_id=1,
        source_name="Ryerson",
        external_record_key="ryerson:possible",
        proposed_fact_key="death:04JUN2021",
    )

    changed=reconcile_discovery_eligibility(db,{1})

    impossible_row=db.execute(
        """
        SELECT state,decision_note
        FROM companion_external_discovery_review
        WHERE id=?
        """,
        (impossible["id"],),
    ).fetchone()

    possible_row=db.execute(
        """
        SELECT state,decision_note
        FROM companion_external_discovery_review
        WHERE id=?
        """,
        (possible["id"],),
    ).fetchone()

    assert changed == 1
    assert impossible_row["state"] == "ineligible"
    assert "before the recorded birth" in impossible_row["decision_note"].lower()
    assert possible_row["state"] == "new"


def test_discovery_reconciliation_keeps_blank_or_undated_fact_new(tmp_path):
    from reunion_companion.companion.ryerson_discovery_review import (
        remember_discovery,
        reconcile_discovery_eligibility,
    )

    db=connect(tmp_path/"x.db")

    person(db,1,"@I1@","David","Smith","David Smith")
    event(db,1,"Birth","23 MAR 1963")
    db.commit()

    blank=remember_discovery(
        db,
        person_id=1,
        source_name="Ryerson",
        external_record_key="ryerson:blank",
        proposed_fact_key="",
    )
    undated=remember_discovery(
        db,
        person_id=1,
        source_name="Ryerson",
        external_record_key="ryerson:undated",
        proposed_fact_key="death:UNKNOWN",
    )

    changed=reconcile_discovery_eligibility(db,{1})

    rows=db.execute(
        """
        SELECT id,state
        FROM companion_external_discovery_review
        WHERE id IN (?,?)
        ORDER BY id
        """,
        (blank["id"],undated["id"]),
    ).fetchall()

    assert changed == 0
    assert [r["state"] for r in rows] == ["new","new"]


def test_discovery_reconciliation_never_overwrites_human_decision(tmp_path):
    from reunion_companion.companion.ryerson_discovery_review import (
        remember_discovery,
        reconcile_discovery_eligibility,
        set_discovery_state,
    )

    db=connect(tmp_path/"x.db")

    person(db,1,"@I1@","David","Smith","David Smith")
    event(db,1,"Birth","23 MAR 1963")
    db.commit()

    discovery=remember_discovery(
        db,
        person_id=1,
        source_name="Ryerson",
        external_record_key="ryerson:decided-impossible",
        proposed_fact_key="death:30APR1942",
    )
    set_discovery_state(
        db,
        discovery["id"],
        "rejected",
        note="Reviewed manually",
    )

    changed=reconcile_discovery_eligibility(db,{1})

    row=db.execute(
        """
        SELECT state,decision_note
        FROM companion_external_discovery_review
        WHERE id=?
        """,
        (discovery["id"],),
    ).fetchone()

    assert changed == 0
    assert row["state"] == "rejected"
    assert row["decision_note"] == "Reviewed manually"


def test_discovery_assembly_skips_currently_ineligible_person(tmp_path):
    from reunion_companion.companion.ryerson_discovery_assembly import (
        assemble_discoveries,
    )

    db = connect(tmp_path/"x.db")

    person(db, 1, "@I1@", "John", "Smith")
    db.commit()

    result = assemble_discoveries(
        db,
        [{
            "person_id": 1,
            "notice_id": "old-smith-notice",
            "death_date": "04 JUN 2021",
            "match_status": "candidate",
        }],
    )

    assert result["assembled_count"] == 0
    assert result["skipped_count"] == 1

    table_exists = db.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type='table'
          AND name='companion_external_discovery_review'
        """
    ).fetchone()

    if table_exists:
        count = db.execute(
            "SELECT COUNT(*) FROM companion_external_discovery_review"
        ).fetchone()[0]
        assert count == 0


def test_discovery_assembly_skips_death_before_birth(tmp_path):
    from reunion_companion.companion.ryerson_discovery_assembly import (
        assemble_discoveries,
    )

    db = connect(tmp_path/"x.db")

    person(db, 1, "@I1@", "David John", "Smith")
    event(db, 1, "Birth", "23 MAR 1963")
    db.commit()

    result = assemble_discoveries(
        db,
        [
            {
                "person_id": 1,
                "notice_id": "impossible",
                "death_date": "30 APR 1942",
                "match_status": "candidate",
            },
            {
                "person_id": 1,
                "notice_id": "possible",
                "death_date": "04 JUN 2021",
                "match_status": "candidate",
            },
        ],
    )

    assert result["assembled_count"] == 1
    assert result["skipped_count"] == 1

    rows = db.execute(
        """
        SELECT external_record_key,proposed_fact_key,state
        FROM companion_external_discovery_review
        ORDER BY external_record_key
        """
    ).fetchall()

    assert len(rows) == 1
    assert rows[0]["external_record_key"] == "ryerson:possible"
    assert rows[0]["proposed_fact_key"] == "death:04 JUN 2021"
    assert rows[0]["state"] == "new"


def test_discovery_assembly_uses_first_parseable_birth_not_first_birth_row(tmp_path):
    from reunion_companion.companion.ryerson_discovery_assembly import (
        assemble_discoveries,
    )

    db = connect(tmp_path/"x.db")

    person(db, 1, "@I1@", "David John", "Smith")

    # The first Birth row is deliberately not a definite date.
    event(db, 1, "Birth", "UNKNOWN")
    event(db, 1, "Birth", "23 MAR 1963")
    db.commit()

    result = assemble_discoveries(
        db,
        [{
            "person_id": 1,
            "notice_id": "pre-birth",
            "death_date": "30 APR 1942",
            "match_status": "candidate",
        }],
    )

    assert result["assembled_count"] == 0
    assert result["skipped_count"] == 1

    table_exists = db.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type='table'
          AND name='companion_external_discovery_review'
        """
    ).fetchone()

    if table_exists:
        count = db.execute(
            "SELECT COUNT(*) FROM companion_external_discovery_review"
        ).fetchone()[0]
        assert count == 0


def test_discovery_reconciliation_uses_first_parseable_birth(tmp_path):
    from reunion_companion.companion.ryerson_discovery_review import (
        remember_discovery,
        reconcile_discovery_eligibility,
    )

    db = connect(tmp_path/"x.db")

    person(db, 1, "@I1@", "David John", "Smith")
    event(db, 1, "Birth", "UNKNOWN")
    event(db, 1, "Birth", "23 MAR 1963")
    db.commit()

    remember_discovery(
        db,
        person_id=1,
        source_name="Ryerson",
        external_record_key="pre-birth-multiple-births",
        proposed_fact_key="death:30 APR 1942",
    )

    changed = reconcile_discovery_eligibility(db, {1})

    assert changed == 1

    row = db.execute(
        """
        SELECT state,decision_note
        FROM companion_external_discovery_review
        WHERE external_record_key='pre-birth-multiple-births'
        """
    ).fetchone()

    assert row["state"] == "ineligible"
    assert "before the recorded birth" in row["decision_note"]
