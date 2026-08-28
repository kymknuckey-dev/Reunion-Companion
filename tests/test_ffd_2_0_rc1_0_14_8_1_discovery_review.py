from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_discovery_review import (
    DISCOVERY_STATES,
    discovery_counts,
    discoveries_for_person,
    reconcile_waiting_discoveries,
    remember_discovery,
    set_discovery_state,
)


def test_discovery_identity_is_persistent_and_deduplicated(tmp_path):
    db = connect(tmp_path / "x.db")

    first = remember_discovery(
        db,
        person_id=17,
        source_name="Ryerson",
        external_record_key="ryerson:abc",
        proposed_fact_key="death:2021-01-02",
        now="2026-08-26T00:00:00+00:00",
    )

    again = remember_discovery(
        db,
        person_id=17,
        source_name="Ryerson",
        external_record_key="ryerson:abc",
        proposed_fact_key="death:2021-01-02",
        now="2026-09-01T00:00:00+00:00",
    )

    assert first["id"] == again["id"]
    assert again["state"] == "new"
    assert discovery_counts(db)["new"] == 1


def test_review_decisions_survive_rediscovery(tmp_path):
    db = connect(tmp_path / "x.db")

    row = remember_discovery(
        db,
        person_id=8,
        source_name="Ryerson",
        external_record_key="notice:99",
        proposed_fact_key="death:1967-03-20",
    )

    set_discovery_state(
        db,
        row["id"],
        "rejected",
        note="Different person",
    )

    again = remember_discovery(
        db,
        person_id=8,
        source_name="Ryerson",
        external_record_key="notice:99",
        proposed_fact_key="death:1967-03-20",
    )

    assert again["state"] == "rejected"
    assert again["decision_note"] == "Different person"


def test_waiting_for_reunion_can_be_confirmed_after_refresh(tmp_path):
    db = connect(tmp_path / "x.db")

    row = remember_discovery(
        db,
        person_id=42,
        source_name="Ryerson",
        external_record_key="notice:rigg",
        proposed_fact_key="death:2021-01-02",
    )

    set_discovery_state(
        db,
        row["id"],
        "waiting_for_reunion",
        note="Accepted; add death date to Reunion",
    )

    confirmed = reconcile_waiting_discoveries(
        db,
        lambda candidate: candidate["proposed_fact_key"] == "death:2021-01-02",
        now="2026-09-10T00:00:00+00:00",
    )

    assert confirmed == [row["id"]]

    final = discoveries_for_person(db, 42)[0]
    assert final["state"] == "confirmed_complete"
    assert final["confirmed_at"] == "2026-09-10T00:00:00+00:00"


def test_deferred_already_known_and_rejected_remain_distinct(tmp_path):
    db = connect(tmp_path / "x.db")

    for i, state in enumerate(
        ("deferred", "already_known", "rejected"),
        start=1,
    ):
        row = remember_discovery(
            db,
            person_id=1,
            source_name="Ryerson",
            external_record_key=f"notice:{i}",
        )
        set_discovery_state(db, row["id"], state)

    rows = discoveries_for_person(db, 1)
    assert [row["state"] for row in rows] == [
        "deferred",
        "already_known",
        "rejected",
    ]

    counts = discovery_counts(db)
    assert all(state in counts for state in DISCOVERY_STATES)


def test_invalid_state_is_rejected(tmp_path):
    db = connect(tmp_path / "x.db")
    row = remember_discovery(
        db,
        person_id=1,
        source_name="Ryerson",
        external_record_key="notice:x",
    )

    try:
        set_discovery_state(db, row["id"], "banana")
    except ValueError as exc:
        assert "unsupported discovery state" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_discovery_fact_present_requires_same_person_event_and_date(tmp_path):
    from reunion_companion.companion.ryerson_discovery_review import (
        discovery_fact_present_in_reunion,
    )

    db = connect(tmp_path / "x.db")

    db.execute(
        """
        INSERT INTO people(
            id,gedcom_xref,reunion_person_id,given_names,surname,
            display_name,sex,raw_name
        ) VALUES(?,?,?,?,?,?,?,?)
        """,
        (42, "@I42@", 42, "Peter", "Rigg", "Peter Rigg", "M", "Peter /Rigg/"),
    )

    db.execute(
        """
        INSERT INTO events(person_id,event_type,date_text,place_text,note_text)
        VALUES(?,?,?,?,?)
        """,
        (42, "Death", "2 JAN 2021", None, None),
    )
    db.commit()

    matching = remember_discovery(
        db,
        person_id=42,
        source_name="Ryerson",
        external_record_key="notice:matching",
        proposed_fact_key="death:2021-01-02",
    )

    wrong_date = remember_discovery(
        db,
        person_id=42,
        source_name="Ryerson",
        external_record_key="notice:wrong-date",
        proposed_fact_key="death:2021-01-03",
    )

    assert discovery_fact_present_in_reunion(db, matching)
    assert not discovery_fact_present_in_reunion(db, wrong_date)


def test_discovery_fact_present_does_not_confirm_indefinite_fact(tmp_path):
    from reunion_companion.companion.ryerson_discovery_review import (
        discovery_fact_present_in_reunion,
    )

    db = connect(tmp_path / "x.db")

    db.execute(
        """
        INSERT INTO people(
            id,gedcom_xref,reunion_person_id,given_names,surname,
            display_name,sex,raw_name
        ) VALUES(?,?,?,?,?,?,?,?)
        """,
        (42, "@I42@", 42, "Peter", "Rigg", "Peter Rigg", "M", "Peter /Rigg/"),
    )

    db.execute(
        """
        INSERT INTO events(person_id,event_type,date_text,place_text,note_text)
        VALUES(?,?,?,?,?)
        """,
        (42, "Death", "ABT 2021", None, None),
    )
    db.commit()

    row = remember_discovery(
        db,
        person_id=42,
        source_name="Ryerson",
        external_record_key="notice:indefinite",
        proposed_fact_key="death:ABT 2021",
    )

    assert not discovery_fact_present_in_reunion(db, row)
