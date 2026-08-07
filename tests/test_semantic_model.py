from reunion_companion.domain import (
    build_genealogy_tree,
    build_reunion_database,
)
from reunion_companion.model import Evidence, Family, Person, ReunionDatabase
from reunion_companion.records import StructuredFamily, StructuredPerson, TreeExtraction


def _extraction() -> TreeExtraction:
    return TreeExtraction(
        package_path="/tmp/probe.familyfile14",
        version="14+",
        people=[
            StructuredPerson(1, "Test", "Probe", "Test Probe", 1, "male", 100, 20),
            StructuredPerson(2, "Mary", "Probe", "Mary Probe", 2, "female", 200, 20),
            StructuredPerson(
                3, "Baby", "Probe", "Baby Probe", 1, "male", 300, 20,
                parent_family_ids=[1],
            ),
        ],
        families=[
            StructuredFamily(
                1, spouse_ids=[1, 2], child_ids=[3],
                spouse_link_status="decoded",
            )
        ],
        warnings=[],
    )


def test_semantic_database_is_canonical_model() -> None:
    database = build_reunion_database(_extraction())
    assert isinstance(database, ReunionDatabase)
    assert isinstance(database.people[1], Person)
    assert isinstance(database.families[1], Family)
    assert database.people[3].parent_ids == [1, 2]
    assert database.people[1].child_ids == [3]


def test_historical_tree_api_returns_same_model() -> None:
    tree = build_genealogy_tree(_extraction())
    assert isinstance(tree, ReunionDatabase)
    assert tree.person_name(2) == "Mary Probe"


def test_database_summary_and_event_search() -> None:
    database = build_reunion_database(_extraction())
    assert database.summary()["people"] == 3
    assert database.summary()["families"] == 1
    assert database.find_events(event_type="birth") == []


def test_evidence_is_json_friendly_dataclass() -> None:
    evidence = Evidence(status="decoded", method="controlled-probe")
    assert evidence.status == "decoded"
