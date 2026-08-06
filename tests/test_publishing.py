from pathlib import Path

from reunion_companion.domain import GenealogyTree, PersonProfile
from reunion_companion.models import Citation, Event, Note, ReunionDate
from reunion_companion.publishing import build_person_profile_markdown


def test_build_markdown_profile() -> None:
    birth = Event(
        event_type="birth",
        date=ReunionDate(
            raw_value=0,
            day=2,
            month=1,
            year=1925,
            year_code=1733,
            high_flags=0,
            display="2 Jan 1925",
        ),
        place="Adelaide, South Australia",
        memo="Probe birth memo",
        citations=[
            Citation(
                source_id=1,
                source_title="Test Probe Birth Certificate",
                detail="Certificate reference TP-1925-001",
            )
        ],
    )
    person = PersonProfile(
        id=1,
        given="Test",
        surname="Probe",
        display="Test Probe",
        sex="male",
        events=[birth],
        spouse_ids=[2],
        child_ids=[3],
        notes=[Note(note_type="person", text="This is the Test Probe person note.")],
    )
    tree = GenealogyTree(
        package_path="/tmp/Probe.familyfile14",
        version="14+",
        people={
            1: person,
            2: PersonProfile(2, "Mary", "Probe", "Mary Probe", "female"),
            3: PersonProfile(3, "Baby", "Probe", "Baby Probe", "male"),
        },
        families={},
        warnings=[],
    )

    markdown = build_person_profile_markdown(tree, person)

    assert "# Test Probe" in markdown
    assert "**Spouses:** Mary Probe" in markdown
    assert "**Children:** Baby Probe" in markdown
    assert "### Birth" in markdown
    assert "**Place:** Adelaide, South Australia" in markdown
    assert "Test Probe Birth Certificate" in markdown
    assert "This is the Test Probe person note." in markdown
