from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_discovery_assembly import (
    assemble_candidate,
    assemble_discoveries,
    external_record_key,
    proposed_fact_key,
)
from reunion_companion.companion.ryerson_discovery_review import (
    discoveries_for_person,
    set_discovery_state,
)


def test_stable_notice_identity_does_not_depend_on_search(tmp_path):
    row = {
        "surname": "Rigg",
        "given_name": "Peter Stanley",
        "death_date": "2021-01-02",
        "publication_date": "2021-01-04",
        "newspaper": "Adelaide Advertiser",
        "notice_type": "Death Notice",
        "search_key": "name:rigg|peter",
    }
    first = external_record_key(row)
    row["search_key"] = "surname:rigg"
    assert external_record_key(row) == first


def test_source_identifier_is_preferred_for_identity():
    assert external_record_key({"notice_id": "ABC123"}) == "ryerson:ABC123"


def test_candidate_requires_concrete_person_association():
    assert assemble_candidate({
        "surname": "Mitchell",
        "given_name": "John",
        "death_date": "2000-01-01",
    }) is None

    assert assemble_candidate({
        "person_id": 12,
        "match_status": "ambiguous",
        "notice_id": "x",
    }) is None

    candidate = assemble_candidate({
        "person_id": 12,
        "match_status": "candidate",
        "notice_id": "x",
        "death_date": "2000-01-01",
    })
    assert candidate is not None
    assert candidate.person_id == 12


def test_fact_key_is_evidence_specific_not_forced_change():
    assert proposed_fact_key({"death_date": "2021-01-02"}) == "death:2021-01-02"
    assert proposed_fact_key({"funeral_date": "2021-01-08"}) == "funeral:2021-01-08"
    assert proposed_fact_key({"publication_date": "2021-01-04"}) == ""


def test_assembly_is_idempotent_and_preserves_review_decision(tmp_path):
    db = connect(tmp_path / "x.db")
    candidates = [{
        "person_id": 42,
        "notice_id": "rigg-2021",
        "death_date": "2021-01-02",
        "match_status": "candidate",
        "match_reason": "Name and death date candidate",
    }]

    first = assemble_discoveries(db, candidates)
    assert first["assembled_count"] == 1

    review = first["assembled"][0]["review"]
    set_discovery_state(
        db,
        review["id"],
        "already_known",
        note="Reunion already contains this death date",
    )

    second = assemble_discoveries(db, candidates)
    assert second["assembled_count"] == 1

    rows = discoveries_for_person(db, 42)
    assert len(rows) == 1
    assert rows[0]["state"] == "already_known"
    assert rows[0]["decision_note"] == "Reunion already contains this death date"


def test_same_notice_can_be_reviewed_against_different_people(tmp_path):
    db = connect(tmp_path / "x.db")
    candidates = [
        {"person_id": 1, "notice_id": "shared", "match_status": "candidate"},
        {"person_id": 2, "notice_id": "shared", "match_status": "candidate"},
    ]

    result = assemble_discoveries(db, candidates)
    assert result["assembled_count"] == 2
    assert len(discoveries_for_person(db, 1)) == 1
    assert len(discoveries_for_person(db, 2)) == 1


def test_unassociated_and_ambiguous_rows_are_skipped(tmp_path):
    db = connect(tmp_path / "x.db")
    result = assemble_discoveries(db, [
        {"notice_id": "a"},
        {"person_id": 3, "notice_id": "b", "match_status": "ambiguous"},
        {"person_id": 4, "notice_id": "c", "match_status": "candidate"},
    ])
    assert result["assembled_count"] == 1
    assert result["skipped_count"] == 2
