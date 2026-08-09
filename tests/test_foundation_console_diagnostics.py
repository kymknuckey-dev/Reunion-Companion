from reunion_companion.foundation import (
    FoundationDatabase,
    FoundationEvent,
    FoundationPerson,
    FoundationQueryEngine,
)
from reunion_companion.foundation.console import answer_question


def _engine() -> FoundationQueryEngine:
    db = FoundationDatabase(warnings=["test warning"])
    person = db.add_person(
        FoundationPerson(
            object_id=1,
            given="Test",
            surname="Probe",
            display_name="Test Probe",
        )
    )
    event = db.add_event(
        FoundationEvent(
            object_id=1,
            event_type="Birth",
            owner_type="person",
            owner_id=1,
        )
    )
    person.events.append(event)
    return FoundationQueryEngine(db)


def test_console_diagnostics_command() -> None:
    answer = answer_question(_engine(), "diagnostics")
    assert "Objects" in answer
    assert "Events" in answer
    assert "Warnings" in answer


def test_console_event_types_command() -> None:
    answer = answer_question(_engine(), "event-types")
    assert "Birth: 1" in answer


def test_console_warnings_command() -> None:
    answer = answer_question(_engine(), "warnings")
    assert "test warning" in answer


def test_console_source_coverage_command() -> None:
    answer = answer_question(_engine(), "source-coverage")
    assert "Sources" in answer
    assert "Citations" in answer
