import pytest

from reunion_companion.companion.database import connect, reset_imported_data
from reunion_companion.companion.external_evidence import (
    add_external_evidence,
    external_evidence_for_person,
    external_evidence_with_current_person,
    set_external_evidence_status,
)


def _person(db, pid, xref, given, surname, display):
    db.execute(
        """
        INSERT INTO people(
            id,gedcom_xref,reunion_person_id,given_names,surname,
            display_name,sex,raw_name
        ) VALUES(?,?,?,?,?,?,?,?)
        """,
        (pid, xref, pid, given, surname, display, "M", f"{given} /{surname}/"),
    )
    db.commit()


def test_peter_rigg_external_evidence_persists_with_name_discrepancy(tmp_path):
    db = connect(tmp_path / "x.sqlite3")
    _person(db, 1, "@I1@", "Peter Stanly", "Rigg", "Peter Stanly Rigg")

    eid = add_external_evidence(
        db,
        person_gedcom_xref="@I1@",
        person_name_snapshot="Peter Stanly Rigg",
        source_name="Ryerson",
        evidence_type="death_notice",
        source_record_name="Peter Stanley Rigg",
        event_type="Death",
        event_date="02JAN2021",
        publication="Adelaide Advertiser",
        publication_date="04JAN2021",
        details="late of Curramulka (born 21 May 1944)",
        birth_date_claim="21 May 1944",
        place_claim="Curramulka",
        match_confidence=99,
        match_reason="Exact birth date and surname; middle name differs Stanly/Stanley.",
    )

    rows = external_evidence_for_person(db, "@I1@")
    assert len(rows) == 1
    assert rows[0]["id"] == eid
    assert rows[0]["source_record_name"] == "Peter Stanley Rigg"
    assert rows[0]["review_status"] == "new"

    set_external_evidence_status(db, eid, "accepted")
    assert external_evidence_for_person(db, "@I1@")[0]["review_status"] == "accepted"


def test_rodney_howie_can_store_death_and_funeral_findings(tmp_path):
    db = connect(tmp_path / "x.sqlite3")
    _person(db, 2, "@I2@", "Rodney Thomas", "Howie", "Rodney Thomas Howie")

    add_external_evidence(
        db,
        person_gedcom_xref="@I2@",
        person_name_snapshot="Rodney Thomas Howie",
        source_name="Ryerson",
        evidence_type="death_notice",
        source_record_name="Rodney Thomas Howie",
        event_type="Death",
        event_date="09JUL2026",
        publication="Adelaide Advertiser",
        publication_date="11JUL2026",
        details="born 07 Oct 1940 Adelaide",
        birth_date_claim="07 Oct 1940",
        place_claim="Adelaide",
        match_confidence=99,
        match_reason="Exact full name and birth details.",
    )
    add_external_evidence(
        db,
        person_gedcom_xref="@I2@",
        person_name_snapshot="Rodney Thomas Howie",
        source_name="Ryerson",
        evidence_type="funeral_notice",
        source_record_name="Rodney Thomas Howie",
        event_type="Funeral",
        event_date="16JUL2026",
        publication="Adelaide Advertiser",
        publication_date="11JUL2026",
        match_confidence=98,
        match_reason="Same full name and publication date as linked death notice.",
    )

    rows = external_evidence_for_person(db, "@I2@")
    assert [r["evidence_type"] for r in rows] == ["death_notice", "funeral_notice"]


def test_gwen_howie_genealogy_sa_findings_support_name_variants(tmp_path):
    db = connect(tmp_path / "x.sqlite3")
    _person(db, 3, "@I3@", "Gwen", "Howie", "Gwen Howie")

    add_external_evidence(
        db,
        person_gedcom_xref="@I3@",
        person_name_snapshot="Gwen Howie",
        source_name="Genealogy SA",
        evidence_type="death_notice",
        source_record_name="Gwendolyn Sophie (Gwennie) (Gwenie) Howie",
        event_type="Death",
        event_date="30-Oct-2017",
        publication_date="02-Nov-2017",
        match_confidence=95,
        match_reason="Surname exact; Gwen is a plausible variant of Gwendolyn.",
    )
    add_external_evidence(
        db,
        person_gedcom_xref="@I3@",
        person_name_snapshot="Gwen Howie",
        source_name="Genealogy SA",
        evidence_type="funeral_notice",
        source_record_name="Gwendolyn Sophie (Gwennie) Howie",
        event_type="Funeral",
        event_date="06-Nov-2017",
        publication_date="02-Nov-2017",
        match_confidence=95,
        match_reason="Same indexed person and publication date as the death notice.",
    )

    rows = external_evidence_for_person(db, "@I3@")
    assert len(rows) == 2
    assert all(r["source_name"] == "Genealogy SA" for r in rows)


def test_reset_imported_data_does_not_erase_external_evidence(tmp_path):
    db = connect(tmp_path / "x.sqlite3")
    _person(db, 7, "@I7@", "Example", "Person", "Example Person")
    add_external_evidence(
        db,
        person_gedcom_xref="@I7@",
        person_name_snapshot="Example Person",
        source_name="Ryerson",
        evidence_type="death_notice",
        event_type="Death",
        event_date="01JAN2020",
    )

    reset_imported_data(db)

    assert db.execute("SELECT COUNT(*) FROM people").fetchone()[0] == 0
    assert len(external_evidence_for_person(db, "@I7@")) == 1


def test_external_evidence_relinks_after_person_is_recreated(tmp_path):
    db = connect(tmp_path / "x.sqlite3")
    _person(db, 10, "@I10@", "Before", "Refresh", "Before Refresh")
    add_external_evidence(
        db,
        person_gedcom_xref="@I10@",
        person_name_snapshot="Before Refresh",
        source_name="Ryerson",
        evidence_type="death_notice",
        event_type="Death",
        event_date="01JAN2020",
    )

    reset_imported_data(db)
    _person(db, 999, "@I10@", "After", "Refresh", "After Refresh")

    rows = external_evidence_with_current_person(db, "@I10@")
    assert len(rows) == 1
    assert rows[0]["current_person_id"] == 999
    assert rows[0]["current_person_name"] == "After Refresh"
    assert rows[0]["person_name_snapshot"] == "Before Refresh"


def test_invalid_status_and_confidence_are_rejected(tmp_path):
    db = connect(tmp_path / "x.sqlite3")

    with pytest.raises(ValueError):
        add_external_evidence(
            db,
            person_gedcom_xref="@I1@",
            person_name_snapshot="X",
            source_name="Ryerson",
            evidence_type="death_notice",
            review_status="maybe",
        )

    with pytest.raises(ValueError):
        add_external_evidence(
            db,
            person_gedcom_xref="@I1@",
            person_name_snapshot="X",
            source_name="Ryerson",
            evidence_type="death_notice",
            match_confidence=101,
        )
