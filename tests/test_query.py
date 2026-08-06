from reunion_companion.domain import GenealogyTree, PersonProfile
from reunion_companion.models import Citation, Event, ReunionDate
from reunion_companion.query import ask_tree


def _tree() -> GenealogyTree:
    birth_test = Event(
        event_type="birth",
        date=ReunionDate(0, 2, 1, 1925, 1733, 0, display="2 Jan 1925"),
        place="Adelaide, South Australia",
        citations=[Citation(1, "Certificate reference TP-1925-001", "Test Probe Birth Certificate")],
    )
    birth_baby = Event(
        event_type="birth",
        date=ReunionDate(0, None, 5, 1976, 1784, 0, display="abt May 1976"),
    )
    return GenealogyTree(
        package_path="/tmp/probe.familyfile14",
        version="14+",
        people={
            1: PersonProfile(1, "Test", "Probe", "Test Probe", "male", events=[birth_test], spouse_ids=[2], child_ids=[3]),
            2: PersonProfile(2, "Mary", "Probe", "Mary Probe", "female", spouse_ids=[1], child_ids=[3]),
            3: PersonProfile(3, "Baby", "Probe", "Baby Probe", "male", events=[birth_baby], parent_ids=[1, 2]),
        },
        families={},
        warnings=[],
    )


def test_children_question() -> None:
    answer = ask_tree(_tree(), "Who are Test Probe's children?")
    assert answer.intent == "person_children"
    assert "Baby Probe" in answer.answer


def test_birth_place_question() -> None:
    answer = ask_tree(_tree(), "Where was Test Probe born?")
    assert answer.intent == "birth_place"
    assert "Adelaide, South Australia" in answer.answer


def test_birth_source_question() -> None:
    answer = ask_tree(_tree(), "What sources support Test Probe's birth?")
    assert answer.intent == "event_sources"
    assert "Test Probe Birth Certificate" in answer.answer
    assert "TP-1925-001" in answer.answer


def test_people_born_in_place() -> None:
    answer = ask_tree(_tree(), "Which people were born in Adelaide?")
    assert answer.intent == "people_born_in"
    assert answer.matched_person_ids == [1]


def test_unsourced_births() -> None:
    answer = ask_tree(_tree(), "List people without a birth source")
    assert answer.intent == "unsourced_births"
    assert "Baby Probe" in answer.answer


def test_unknown_question_is_honest() -> None:
    answer = ask_tree(_tree(), "What was Test Probe's favourite food?")
    assert answer.intent == "unknown"
    assert answer.confidence == "low"
