from reunion_companion.domain import build_genealogy_tree
from reunion_companion.models import Event
from reunion_companion.records import StructuredFamily, StructuredPerson, TreeExtraction


def _extraction() -> TreeExtraction:
    return TreeExtraction(
        package_path="/tmp/probe.familyfile14",
        version="14+",
        people=[
            StructuredPerson(1, "Test", "Probe", "Test Probe", 1, "male", 100, 20, events=[Event("birth")]),
            StructuredPerson(2, "Mary", "Probe", "Mary Probe", 2, "female", 200, 20),
            StructuredPerson(3, "Baby", "Probe", "Baby Probe", 1, "male", 300, 20, parent_family_ids=[1]),
        ],
        families=[StructuredFamily(1, spouse_ids=[1, 2], child_ids=[3], spouse_link_status="decoded")],
        warnings=[],
    )


def test_build_relationships() -> None:
    tree = build_genealogy_tree(_extraction())
    assert tree.people[1].spouse_ids == [2]
    assert tree.people[2].spouse_ids == [1]
    assert tree.people[1].child_ids == [3]
    assert tree.people[3].parent_ids == [1, 2]


def test_find_people() -> None:
    tree = build_genealogy_tree(_extraction())
    assert [person.id for person in tree.find_people("mary")] == [2]
    assert [person.id for person in tree.find_people("probe")] == [1, 2, 3]


def test_tree_serialisation_uses_ids_as_keys() -> None:
    tree = build_genealogy_tree(_extraction())
    result = tree.to_dict()
    assert "1" in result["people"]
    assert "1" in result["families"]
