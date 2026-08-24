from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence_matcher import (
    match_external_evidence,
    missing_death_candidates,
    person_identity_profile,
)


def _person(db, pid, xref, given, surname, display, sex="M"):
    db.execute(
        """
        INSERT INTO people(
            id,gedcom_xref,reunion_person_id,given_names,surname,
            display_name,sex,raw_name
        ) VALUES(?,?,?,?,?,?,?,?)
        """,
        (pid, xref, pid, given, surname, display, sex, f"{given} /{surname}/"),
    )


def _event(db, pid, etype, date=None, place=None):
    db.execute(
        """
        INSERT INTO events(person_id,event_type,date_text,place_text)
        VALUES(?,?,?,?)
        """,
        (pid, etype, date, place),
    )


def _family(db, fid, *members):
    db.execute("INSERT INTO families(id,gedcom_xref) VALUES(?,?)", (fid, f"@F{fid}@"))
    for pid, role in members:
        db.execute(
            "INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,?)",
            (fid, pid, role),
        )


def test_missing_death_candidates_use_existing_research_gap_logic(tmp_path):
    db = connect(tmp_path / "x.sqlite3")
    _person(db, 1, "@I1@", "Peter Stanly", "Rigg", "Peter Stanly Rigg")
    _event(db, 1, "Birth", "21 May 1944", "Brighton Community Hospital")

    _person(db, 2, "@I2@", "Already", "Dead", "Already Dead")
    _event(db, 2, "Birth", "01 Jan 1900", "Adelaide")
    death_id = db.execute(
        "INSERT INTO events(person_id,event_type,date_text,place_text) VALUES(?,?,?,?)",
        (2, "Death", "01 Jan 1980", "Adelaide"),
    ).lastrowid
    db.execute("INSERT INTO sources(id,gedcom_xref,title) VALUES(1,'@S1@','Death source')")
    db.execute(
        "INSERT INTO event_sources(event_id,source_id,relation) VALUES(?,1,'GEDCOM')",
        (death_id,),
    )
    db.commit()

    rows = missing_death_candidates(db)
    assert [r["gedcom_xref"] for r in rows] == ["@I1@"]
    assert rows[0]["birth_date"] == "21 May 1944"


def test_person_identity_profile_includes_family_context(tmp_path):
    db = connect(tmp_path / "x.sqlite3")
    _person(db, 1, "@I1@", "Peter Stanly", "Rigg", "Peter Stanly Rigg")
    _person(db, 2, "@I2@", "Jillian Marie", "Cox", "Jillian Marie Cox", "F")
    _person(db, 3, "@I3@", "Leah Sharon", "Rigg", "Leah Sharon Rigg", "F")
    _person(db, 4, "@I4@", "Troy Steven", "Rigg", "Troy Steven Rigg")
    _event(db, 1, "Birth", "21 May 1944", "Brighton Community Hospital")
    _family(db, 1, (1, "Husband"), (2, "Wife"), (3, "Child"), (4, "Child"))
    db.commit()

    p = person_identity_profile(db, 1)
    assert p["spouses"] == ["Jillian Marie Cox"]
    assert set(p["children"]) == {"Leah Sharon Rigg", "Troy Steven Rigg"}


def test_peter_rigg_exact_birth_date_overcomes_middle_name_spelling_error(tmp_path):
    db = connect(tmp_path / "x.sqlite3")
    _person(db, 1, "@I1@", "Peter Stanly", "Rigg", "Peter Stanly Rigg")
    _event(db, 1, "Birth", "21 May 1944", "Brighton Community Hospital")
    db.commit()

    result = match_external_evidence(
        db,
        1,
        {
            "source_record_name": "Peter Stanley Rigg",
            "birth_date_claim": "21 May 1944",
            "place_claim": "Curramulka",
            "details": "late of Curramulka (born 21 May 1944)",
        },
    )

    assert result.status == "high_confidence"
    assert result.score >= 80
    assert "birth date exact" in result.reasons
    assert "middle name near-match" in result.reasons


def test_rodney_howie_exact_name_and_birth_date_is_high_confidence(tmp_path):
    db = connect(tmp_path / "x.sqlite3")
    _person(db, 1, "@I1@", "Rodney Thomas", "Howie", "Rodney Thomas Howie")
    _event(db, 1, "Birth", "07 Oct 1940", "Adelaide")
    db.commit()

    result = match_external_evidence(
        db,
        1,
        {
            "source_record_name": "Rodney Thomas Howie",
            "birth_date_claim": "07 Oct 1940",
            "place_claim": "Adelaide",
            "details": "(born 07 Oct 1940 Adelaide)",
        },
    )

    assert result.status == "high_confidence"
    assert result.score == 100


def test_gwen_howie_name_variant_without_birth_date_needs_review(tmp_path):
    db = connect(tmp_path / "x.sqlite3")
    _person(db, 1, "@I1@", "Gwen", "Howie", "Gwen Howie", "F")
    db.commit()

    result = match_external_evidence(
        db,
        1,
        {
            "source_record_name": "Gwendolyn Sophie (Gwennie) (Gwenie) Howie",
            "details": "",
        },
    )

    assert result.status == "reject"
    assert result.score < 55


def test_family_relationships_can_raise_a_name_match_to_review(tmp_path):
    db = connect(tmp_path / "x.sqlite3")
    _person(db, 1, "@I1@", "John", "Smith", "John Smith")
    _person(db, 2, "@I2@", "Mary", "Smith", "Mary Smith", "F")
    _person(db, 3, "@I3@", "Anne", "Smith", "Anne Smith", "F")
    _family(db, 1, (1, "Husband"), (2, "Wife"), (3, "Child"))
    db.commit()

    result = match_external_evidence(
        db,
        1,
        {
            "source_record_name": "John Smith",
            "details": "Loved husband of Mary Smith and father of Anne Smith.",
        },
    )

    assert result.status in {"needs_review", "high_confidence"}
    assert "spouse corroborated" in result.reasons
    assert "child corroborated" in result.reasons


def test_conflicting_birth_date_rejects_even_an_exact_name(tmp_path):
    db = connect(tmp_path / "x.sqlite3")
    _person(db, 1, "@I1@", "John", "Smith", "John Smith")
    _event(db, 1, "Birth", "01 Jan 1940", "Adelaide")
    db.commit()

    result = match_external_evidence(
        db,
        1,
        {
            "source_record_name": "John Smith",
            "birth_date_claim": "01 Jan 1955",
        },
    )

    assert result.status == "reject"
    assert "birth date conflicts" in result.contradictions


def test_common_name_without_corrobation_is_not_high_confidence(tmp_path):
    db = connect(tmp_path / "x.sqlite3")
    _person(db, 1, "@I1@", "John", "Smith", "John Smith")
    db.commit()

    result = match_external_evidence(
        db,
        1,
        {
            "source_record_name": "John Smith",
        },
    )

    assert result.status == "needs_review"
    assert result.score == 75
