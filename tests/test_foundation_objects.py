from reunion_companion.foundation import (
    FoundationEvent,
    FoundationFamily,
    FoundationPerson,
    FoundationPlace,
)


def _person(person_id: int, given: str, surname: str = "Probe") -> FoundationPerson:
    return FoundationPerson(object_id=person_id, given=given, surname=surname)


def test_person_full_name_and_display_override() -> None:
    person = _person(1, "Test")
    assert person.full_name == "Test Probe"

    person.display_name = "T. Probe"
    assert person.full_name == "T. Probe"


def test_family_relationship_navigation() -> None:
    father = _person(1, "Test")
    mother = _person(2, "Mary")
    child = _person(3, "Baby")

    family = FoundationFamily(
        object_id=1,
        spouses=[father, mother],
        children=[child],
    )
    father.spouse_families.append(family)
    mother.spouse_families.append(family)
    child.parent_families.append(family)

    assert father.spouses == [mother]
    assert father.children == [child]
    assert child.parents == [father, mother]


def test_person_relationship_navigation_deduplicates() -> None:
    first = _person(1, "Test")
    second = _person(2, "Mary")
    child = _person(3, "Baby")

    family = FoundationFamily(
        object_id=1,
        spouses=[first, second],
        children=[child],
    )
    first.spouse_families.extend([family, family])

    assert first.spouses == [second]
    assert first.children == [child]


def test_family_add_methods_do_not_duplicate_people() -> None:
    family = FoundationFamily(object_id=1)
    person = _person(1, "Test")

    family.add_spouse(person)
    family.add_spouse(person)
    family.add_child(person)
    family.add_child(person)

    assert family.spouses == [person]
    assert family.children == [person]


def test_event_links_to_place() -> None:
    place = FoundationPlace(object_id=1, name="Adelaide, South Australia")
    event = FoundationEvent(
        object_id=10,
        event_type="birth",
        date_text="2 Jan 1925",
        place=place,
    )

    assert event.label == "Birth"
    assert event.has_date is True
    assert event.has_place is True
    assert str(event) == "Birth — 2 Jan 1925 — Adelaide, South Australia"


def test_place_coordinate_state() -> None:
    unresolved = FoundationPlace(object_id=1, name="Adelaide")
    resolved = FoundationPlace(
        object_id=2,
        name="Adelaide Registry Office",
        latitude=-34.9285,
        longitude=138.6007,
    )

    assert unresolved.has_coordinates is False
    assert resolved.has_coordinates is True


def test_person_event_filter_is_case_insensitive() -> None:
    person = _person(1, "Test")
    birth = FoundationEvent(object_id=1, event_type="Birth")
    marriage = FoundationEvent(object_id=2, event_type="marriage")
    person.events.extend([birth, marriage])

    assert person.events_by_type("birth") == [birth]
    assert person.events_by_type("MARRIAGE") == [marriage]


def test_family_event_filter_is_case_insensitive() -> None:
    family = FoundationFamily(object_id=1)
    marriage = FoundationEvent(object_id=1, event_type="Marriage")
    family.events.append(marriage)

    assert family.events_by_type("marriage") == [marriage]
