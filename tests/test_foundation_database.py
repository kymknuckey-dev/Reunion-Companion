from reunion_companion.foundation import (
    FoundationDatabase,
    FoundationEvent,
    FoundationFamily,
    FoundationPerson,
    FoundationPlace,
)


def _person(person_id: int, given: str, surname: str = "Probe") -> FoundationPerson:
    return FoundationPerson(object_id=person_id, given=given, surname=surname)


def test_database_add_and_lookup_objects() -> None:
    db = FoundationDatabase()

    person = db.add_person(_person(1, "Test"))
    family = db.add_family(FoundationFamily(object_id=1))
    place = db.add_place(FoundationPlace(object_id=1, name="Adelaide"))
    event = db.add_event(
        FoundationEvent(
            object_id=1,
            event_type="birth",
            place=place,
            owner_type="person",
            owner_id=1,
        )
    )

    assert db.person(1) is person
    assert db.family(1) is family
    assert db.place(1) is place
    assert db.event(1) is event
    assert db.object_counts == {
        "people": 1,
        "families": 1,
        "events": 1,
        "places": 1,
    }


def test_database_name_indexes_are_case_and_space_insensitive() -> None:
    db = FoundationDatabase()
    test = db.add_person(_person(1, "Test"))
    mary = db.add_person(_person(2, "Mary"))
    adelaide = db.add_place(
        FoundationPlace(object_id=1, name="Adelaide, South Australia")
    )

    assert db.find_people_by_name("  TEST   PROBE ") == [test]
    assert db.find_people_by_surname("probe") == [test, mary]
    assert db.find_places_by_name("adelaide, south australia") == [adelaide]


def test_database_rebuild_indexes_after_direct_repository_changes() -> None:
    db = FoundationDatabase()
    person = _person(1, "Test")
    db.people.add(person)

    assert db.find_people_by_name("Test Probe") == []

    db.rebuild_indexes()

    assert db.find_people_by_name("Test Probe") == [person]
