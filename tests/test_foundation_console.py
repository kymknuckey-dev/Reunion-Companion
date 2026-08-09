from reunion_companion.foundation.console import answer_question
from reunion_companion.foundation import (
    FoundationDatabase,
    FoundationEvent,
    FoundationPerson,
    FoundationPlace,
    FoundationQueryEngine,
)


def _engine() -> FoundationQueryEngine:
    db = FoundationDatabase()
    place = db.add_place(FoundationPlace(object_id=1, name="Adelaide, South Australia"))
    person = db.add_person(
        FoundationPerson(object_id=1, given="Test", surname="Probe", display_name="Test Probe")
    )
    event = db.add_event(
        FoundationEvent(
            object_id=1,
            event_type="Birth",
            date_text="2 Jan 1925",
            place=place,
            owner_type="person",
            owner_id=1,
        )
    )
    person.events.append(event)
    return FoundationQueryEngine(db)


def test_console_stats() -> None:
    answer = answer_question(_engine(), "how many people are in the database?")
    assert answer == "People: 1"


def test_console_person_summary() -> None:
    answer = answer_question(_engine(), "tell me about Test Probe")
    assert "Test Probe" in answer
    assert "Birth — 2 Jan 1925 — Adelaide, South Australia" in answer


def test_console_birth_place_question() -> None:
    answer = answer_question(_engine(), "which people were born in Adelaide?")
    assert "Test Probe" in answer


def test_console_unknown_is_honest() -> None:
    answer = answer_question(_engine(), "what colour was Test's bicycle?")
    assert "don't yet have a deterministic Beta 1 query" in answer
