from datetime import date

from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence_matcher import (
    ryerson_birth_eligible,
    ryerson_death_candidates,
)


def add_person(db, pid, name, birth=None):
    bits = name.split()

    db.execute(
        """
        INSERT INTO people(
            id,gedcom_xref,reunion_person_id,
            given_names,surname,display_name,sex,raw_name
        )
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            pid,
            f"@I{pid}@",
            pid,
            " ".join(bits[:-1]),
            bits[-1],
            name,
            "U",
            name,
        ),
    )

    if birth is not None:
        db.execute(
            """
            INSERT INTO events(
                person_id,event_type,date_text
            )
            VALUES(?,?,?)
            """,
            (pid, "Birth", birth),
        )

    db.commit()


def test_birth_gate_excludes_missing_date():
    today = date(2026, 8, 27)

    assert not ryerson_birth_eligible(None, today=today)
    assert not ryerson_birth_eligible("", today=today)


def test_birth_gate_excludes_potential_age_over_100():
    today = date(2026, 8, 27)

    assert ryerson_birth_eligible("1926", today=today)
    assert ryerson_birth_eligible("27 AUG 1926", today=today)

    assert not ryerson_birth_eligible("1925", today=today)
    assert not ryerson_birth_eligible("01 JAN 1900", today=today)


def test_uncertain_birth_kept_when_latest_possible_year_is_within_window():
    today = date(2026, 8, 27)

    assert ryerson_birth_eligible(
        "BET 1920 AND 1930",
        today=today,
    )


def test_ryerson_candidate_gate(tmp_path):
    db = connect(tmp_path / "x.db")

    add_person(db, 1, "No Birth")
    add_person(db, 2, "Too Old", "01 JAN 1900")
    add_person(db, 3, "Eligible Person", "01 JAN 1950")

    rows = ryerson_death_candidates(db)

    assert [r["display_name"] for r in rows] == [
        "Eligible Person"
    ]


def test_incomplete_death_semantics_are_retained(tmp_path):
    db = connect(tmp_path / "x.db")

    add_person(db, 1, "Peter Rigg", "21 MAY 1944")

    db.execute(
        """
        INSERT INTO events(
            person_id,event_type,note_text
        )
        VALUES(?,?,?)
        """,
        (
            1,
            "Death",
            "Death notice 02 JAN 2021",
        ),
    )

    db.commit()

    row = ryerson_death_candidates(db)[0]

    assert row["death_state"] == "incomplete"
    assert "Death date not recorded" in row["death_reasons"]
    assert "Death place not recorded" in row["death_reasons"]
    assert "No linked death evidence" in row["death_reasons"]
