from reunion_companion.event_engine import (
    EventEngine,
    event_definition,
    normalise_event_type,
)
from reunion_companion.model import (
    Citation,
    Event,
    Family,
    Person,
    ReunionDatabase,
    ReunionDate,
)


def _date(year: int, month: int | None = None, day: int | None = None) -> ReunionDate:
    return ReunionDate(
        raw_value=0,
        day=day,
        month=month,
        year=year,
        year_code=year - 192,
        high_flags=0,
        display=(
            f"{day} Jan {year}" if day and month == 1
            else f"Jan {year}" if month == 1
            else str(year)
        ),
    )


def _database() -> ReunionDatabase:
    birth = Event(
        "birth",
        date=_date(1925, 1, 2),
        place="Adelaide, South Australia",
        citations=[Citation(1, source_title="Birth Certificate")],
    )
    death = Event("death", date=_date(2000), place="Adelaide")
    marriage = Event("marriage", date=_date(1950), place="Registry Office")

    people = {
        1: Person(1, "Test", "Probe", "Test Probe", "male", events=[birth, death]),
        2: Person(2, "Mary", "Probe", "Mary Probe", "female"),
        3: Person(3, "Baby", "Probe", "Baby Probe", "male"),
    }
    people[1].spouse_ids = [2]
    people[2].spouse_ids = [1]
    people[1].child_ids = [3]
    people[2].child_ids = [3]
    people[3].parent_ids = [1, 2]

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
    )


def test_event_registry_aliases() -> None:
    assert normalise_event_type("Born") == "birth"
    assert normalise_event_type("Military Service") == "military_service"
    assert event_definition("death").label == "Death"


def test_all_events_are_generic_occurrences() -> None:
    events = EventEngine(_database()).all_events()
    assert [item.event_type for item in events] == [
        "birth", "marriage", "death"
    ]
    assert events[1].owner_type == "family"


def test_search_filters_type_place_year_and_source() -> None:
    engine = EventEngine(_database())

    assert len(engine.search(event_type="born")) == 1
    assert len(engine.search(place="registry")) == 1
    assert len(engine.search(year_from=1940, year_to=1960)) == 1
    assert [item.event_type for item in engine.search(sourced=True)] == ["birth"]
    assert {item.event_type for item in engine.search(sourced=False)} == {
        "marriage", "death"
    }


def test_person_timeline_includes_own_marriage_but_not_parents_marriage() -> None:
    engine = EventEngine(_database())

    assert [item.event_type for item in engine.timeline(1)] == [
        "birth", "marriage", "death"
    ]
    assert engine.timeline(3) == []


def test_person_event_only_timeline() -> None:
    engine = EventEngine(_database())
    assert [item.event_type for item in engine.timeline(
        1, include_family_events=False
    )] == ["birth", "death"]


def test_registry_reports_decoded_and_pending_types() -> None:
    status = EventEngine(_database()).registry_status()
    by_key = {item["key"]: item for item in status}

    assert by_key["birth"]["decoded_count"] == 1
    assert by_key["marriage"]["decoded_count"] == 1
    assert by_key["death"]["decoded_count"] == 1
    assert by_key["burial"]["decoded_count"] == 0
    assert by_key["burial"]["decoder_status"] == "registered"


def test_summary() -> None:
    summary = EventEngine(_database()).summary()
    assert summary["total_events"] == 3
    assert summary["person_events"] == 2
    assert summary["family_events"] == 1
    assert summary["sourced_events"] == 1
