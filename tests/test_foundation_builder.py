from reunion_companion.foundation import FoundationBuilder
from reunion_companion.model import Event, Family, Person, Place, ReunionDatabase
from reunion_companion.model.event import ReunionDate


def _semantic_database() -> ReunionDatabase:
    birth_date = ReunionDate(
        raw_value=0,
        day=2,
        month=1,
        year=1925,
        year_code=0,
        high_flags=0,
        display="2 Jan 1925",
    )
    marriage_date = ReunionDate(
        raw_value=0,
        day=3,
        month=3,
        year=1950,
        year_code=0,
        high_flags=0,
        display="3 Mar 1950",
    )

    people = {
        1: Person(
            id=1,
            given="Test",
            surname="Probe",
            display="Test Probe",
            sex="male",
            events=[
                Event(
                    event_type="Birth",
                    date=birth_date,
                    place_id=1,
                    place="Adelaide, South Australia",
                    memo="Probe birth memo",
                    raw_offset=123,
                    decode_status="decoded-controlled-probes",
                )
            ],
        ),
        2: Person(
            id=2,
            given="Mary",
            surname="Probe",
            display="Mary Probe",
            sex="female",
        ),
        3: Person(
            id=3,
            given="Baby",
            surname="Probe",
            display="Baby Probe",
            sex="male",
            parent_family_ids=[1],
        ),
    }

    families = {
        1: Family(
            id=1,
            spouse_ids=[1, 2],
            child_ids=[3],
            events=[
                Event(
                    event_type="Marriage",
                    date=marriage_date,
                    place_id=2,
                    place="Adelaide Registry Office",
                    decode_status="decoded-controlled-probes",
                )
            ],
        )
    }

    return ReunionDatabase(
        package_path="/tmp/Probe.familyfile14",
        version="14+",
        people=people,
        families=families,
        warnings=["controlled probe"],
        places={
            1: Place(id=1, name="Adelaide, South Australia"),
            2: Place(id=2, name="Adelaide Registry Office"),
        },
    )


def test_builder_preserves_package_metadata_and_counts() -> None:
    db, report = FoundationBuilder().build_with_report(_semantic_database())

    assert db.package_path == "/tmp/Probe.familyfile14"
    assert db.version == "14+"
    assert db.warnings == ["controlled probe"]
    assert db.object_counts == {
        "people": 3,
        "families": 1,
        "events": 2,
        "places": 2,
        "notes": 0,
        "media": 0,
        "sources": 0,
        "citations": 0,
    }
    assert report.to_dict() == {
        "people": 3,
        "families": 1,
        "events": 2,
        "places": 2,
        "notes": 0,
        "media": 0,
        "sources": 0,
        "citations": 0,
        "warnings": 1,
    }


def test_builder_creates_linked_relationship_graph() -> None:
    db = FoundationBuilder().build(_semantic_database())

    test = db.person(1)
    mary = db.person(2)
    baby = db.person(3)

    assert test.spouses == [mary]
    assert mary.spouses == [test]
    assert test.children == [baby]
    assert baby.parents == [test, mary]


def test_builder_converts_person_and_family_events() -> None:
    db = FoundationBuilder().build(_semantic_database())

    birth = db.person(1).events[0]
    marriage = db.family(1).events[0]

    assert birth.id == 1
    assert birth.event_type == "Birth"
    assert birth.date_text == "2 Jan 1925"
    assert birth.place is db.place(1)
    assert birth.display_place == "Adelaide, South Australia"
    assert birth.owner_type == "person"
    assert birth.owner_id == 1
    assert birth.source_offset == 123

    assert marriage.id == 2
    assert marriage.event_type == "Marriage"
    assert marriage.date_text == "3 Mar 1950"
    assert marriage.place is db.place(2)
    assert marriage.owner_type == "family"
    assert marriage.owner_id == 1


def test_builder_event_ids_are_deterministic() -> None:
    source = _semantic_database()
    first = FoundationBuilder().build(source)
    second = FoundationBuilder().build(source)

    assert first.events.ids() == [1, 2]
    assert second.events.ids() == [1, 2]


def test_builder_populates_search_indexes() -> None:
    db = FoundationBuilder().build(_semantic_database())

    assert [person.id for person in db.find_people_by_surname("probe")] == [1, 2, 3]
    assert [place.id for place in db.find_places_by_name("adelaide registry office")] == [2]


def test_builder_preserves_unresolved_place_text() -> None:
    source = _semantic_database()
    source.people[2].events.append(
        Event(
            event_type="Residence",
            place="Somewhere not in places.cache",
        )
    )

    db = FoundationBuilder().build(source)
    residence = db.person(2).events[0]

    assert residence.place is None
    assert residence.place_text == "Somewhere not in places.cache"
    assert residence.has_place is True
