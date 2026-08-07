from reunion_companion.model import Family, Person, ReunionDatabase
from reunion_companion.relationships import RelationshipEngine, cousin_term


def _person(person_id: int, name: str) -> Person:
    given, surname = name.split(" ", 1)
    return Person(person_id, given, surname, name, None)


def _database() -> ReunionDatabase:
    # Grandparents 1/2
    # ├── Parent A 3 ─ spouse 5
    # │   └── Child A 6
    # └── Parent B 4 ─ spouse 7
    #     └── Child B 8
    people = {
        1: _person(1, "Grand Father"),
        2: _person(2, "Grand Mother"),
        3: _person(3, "Parent Alpha"),
        4: _person(4, "Parent Beta"),
        5: _person(5, "Spouse Alpha"),
        6: _person(6, "Child Alpha"),
        7: _person(7, "Spouse Beta"),
        8: _person(8, "Child Beta"),
        9: _person(9, "Isolated Person"),
    }
    families = {
        1: Family(1, spouse_ids=[1, 2], child_ids=[3, 4]),
        2: Family(2, spouse_ids=[3, 5], child_ids=[6]),
        3: Family(3, spouse_ids=[4, 7], child_ids=[8]),
    }

    for family in families.values():
        for spouse_id in family.spouse_ids:
            person = people[spouse_id]
            person.spouse_ids.extend(
                item for item in family.spouse_ids
                if item != spouse_id and item not in person.spouse_ids
            )
            person.child_ids.extend(
                item for item in family.child_ids
                if item not in person.child_ids
            )
        for child_id in family.child_ids:
            child = people[child_id]
            child.parent_ids.extend(
                item for item in family.spouse_ids
                if item not in child.parent_ids
            )

    return ReunionDatabase(
        package_path="/tmp/test.familyfile14",
        version="14+",
        people=people,
        families=families,
        warnings=[],
    )


def test_ancestors_and_descendants() -> None:
    engine = RelationshipEngine(_database())

    assert [(item.person_id, item.generations) for item in engine.ancestors(6)] == [
        (3, 1),
        (5, 1),
        (1, 2),
        (2, 2),
    ]
    assert [(item.person_id, item.generations) for item in engine.descendants(1)] == [
        (3, 1),
        (4, 1),
        (6, 2),
        (8, 2),
    ]


def test_direct_relationships() -> None:
    engine = RelationshipEngine(_database())

    assert engine.shortest_path(3, 6).label == "child"
    assert engine.shortest_path(6, 3).label == "parent"
    assert engine.shortest_path(3, 5).label == "spouse"
    assert engine.shortest_path(3, 4).label == "sibling"


def test_first_cousins_and_common_ancestors() -> None:
    engine = RelationshipEngine(_database())
    path = engine.shortest_path(6, 8)

    assert path is not None
    assert path.label == "1st cousin"
    assert path.blood_relationship == "1st cousin"
    assert path.common_ancestor_ids == [1, 2]
    assert path.generation_distances == (2, 2)
    assert path.uses_spouse_link is False


def test_ancestor_terms_from_first_person_perspective() -> None:
    engine = RelationshipEngine(_database())

    assert engine.shortest_path(1, 6).label == "grandchild"
    assert engine.shortest_path(6, 1).label == "grandparent"


def test_spouse_path_and_blood_only() -> None:
    engine = RelationshipEngine(_database())

    path = engine.shortest_path(5, 8)
    assert path is not None
    assert path.uses_spouse_link is True

    blood_path = engine.shortest_path(5, 8, include_spouses=False)
    assert blood_path is None


def test_connected_components() -> None:
    components = RelationshipEngine(_database()).connected_components()

    assert [len(component.person_ids) for component in components] == [8, 1]
    assert components[1].person_ids == [9]


def test_cousin_term_removed() -> None:
    assert cousin_term(2, 0) == "2nd cousin"
    assert cousin_term(2, 1) == "2nd cousin once removed"
    assert cousin_term(3, 2) == "3rd cousin 2 times removed"
