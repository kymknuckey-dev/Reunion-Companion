from reunion_companion.model import Event, Family, Person, Place, ReunionDatabase
from reunion_companion.place_engine import PlaceEngine


def _database() -> ReunionDatabase:
    birth = Event("birth", place_id=1, place="Adelaide, South Australia")
    marriage = Event("marriage", place_id=2, place="Adelaide Registry Office")

    people = {
        1: Person(1, "Test", "Probe", "Test Probe", "male", events=[birth]),
        2: Person(2, "Mary", "Probe", "Mary Probe", "female"),
        3: Person(3, "Baby", "Probe", "Baby Probe", "male"),
    }
    return ReunionDatabase(
        package_path="/tmp/probe.familyfile14",
        version="14+",
        people=people,
        families={
            1: Family(
                1,
                spouse_ids=[1, 2],
                child_ids=[3],
                events=[marriage],
            )
        },
        warnings=[],
        places={
            1: Place(1, "Adelaide, South Australia"),
            2: Place(2, "Adelaide Registry Office"),
            3: Place(3, "Unused Place"),
        },
    )


def test_place_search() -> None:
    engine = PlaceEngine(_database())
    assert [place.id for place in engine.find("registry")] == [2]
    assert [place.id for place in engine.find("adelaide")] == [2, 1]


def test_place_usage_and_summary() -> None:
    engine = PlaceEngine(_database())

    first = engine.summary(1)
    assert first.usage_count == 1
    assert first.person_event_count == 1
    assert first.people_ids == [1]
    assert first.event_types == {"birth": 1}

    second = engine.summary(2)
    assert second.family_event_count == 1
    assert second.people_ids == [1, 2]
    assert second.family_ids == [1]
    assert second.event_types == {"marriage": 1}


def test_unused_places() -> None:
    assert [place.id for place in PlaceEngine(_database()).unused_places()] == [3]


def test_coverage() -> None:
    coverage = PlaceEngine(_database()).coverage()
    assert coverage["total_places"] == 3
    assert coverage["used_places"] == 2
    assert coverage["unused_places"] == 1
    assert coverage["event_place_links"] == 2
    assert coverage["hierarchy_status"] == "not-decoded"


def test_missing_place_raises_clean_keyerror() -> None:
    engine = PlaceEngine(_database())
    try:
        engine.summary(99)
    except KeyError as exc:
        assert exc.args[0] == "Place 99 was not found"
    else:
        raise AssertionError("Expected KeyError")
