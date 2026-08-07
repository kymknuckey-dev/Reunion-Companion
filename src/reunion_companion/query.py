from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Iterable

from .event_engine import event_definition, normalise_event_type
from .domain import load_reunion_database
from .model import Person, ReunionDatabase


@dataclass(slots=True)
class Evidence:
    kind: str
    person_id: int | None = None
    person_name: str | None = None
    event_type: str | None = None
    field: str | None = None
    value: str | None = None
    source_id: int | None = None
    source_title: str | None = None
    citation_detail: str | None = None


@dataclass(slots=True)
class Answer:
    question: str
    intent: str
    answer: str
    evidence: list[Evidence] = field(default_factory=list)
    matched_person_ids: list[int] = field(default_factory=list)
    confidence: str = "high"
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_RELATION_PATTERNS = (
    (re.compile(r"^(?:who (?:are|is) )?(.+?)(?:'s|’s) children\??$", re.I), "children"),
    (re.compile(r"^(?:who (?:are|is) )?(.+?)(?:'s|’s) parents\??$", re.I), "parents"),
    (re.compile(r"^(?:who (?:is|was) )?(.+?)(?:'s|’s) spouse\??$", re.I), "spouses"),
    (re.compile(r"^(?:who (?:are|were) )?(.+?)(?:'s|’s) spouses\??$", re.I), "spouses"),
)


def _normalise_name(text: str) -> str:
    return text.strip().strip("?.! ")


def _find_unique_person(tree: ReunionDatabase, name: str) -> tuple[Person | None, list[Person]]:
    matches = tree.find_people(_normalise_name(name))
    if len(matches) == 1:
        return matches[0], matches
    exact = [person for person in matches if person.display.casefold() == _normalise_name(name).casefold()]
    if len(exact) == 1:
        return exact[0], matches
    return None, matches


def _event(person: Person, event_type: str):
    return next((event for event in person.events if event.event_type.casefold() == event_type.casefold()), None)


def _relationship_answer(tree: ReunionDatabase, question: str, name: str, relation: str) -> Answer:
    person, matches = _find_unique_person(tree, name)
    if person is None:
        if not matches:
            return Answer(
                question=question,
                intent=f"person_{relation}",
                answer=f"No person matching ‘{_normalise_name(name)}’ was found in the decoded Reunion data.",
                confidence="high",
            )
        names = ", ".join(f"{item.display} (Person {item.id})" for item in matches)
        return Answer(
            question=question,
            intent=f"person_{relation}",
            answer=f"The name is ambiguous. Matching people: {names}.",
            matched_person_ids=[item.id for item in matches],
            confidence="low",
            limitations=["Choose a Person ID or use the full stored name."],
        )

    ids = {
        "children": person.child_ids,
        "parents": person.parent_ids,
        "spouses": person.spouse_ids,
    }[relation]
    labels = [tree.person_name(item) for item in ids]
    singular = {"children": "child", "parents": "parent", "spouses": "spouse"}[relation]
    if labels:
        answer_text = f"{person.display} has {len(labels)} decoded {singular}{'' if len(labels) == 1 else 's'}: " + ", ".join(labels) + "."
    else:
        answer_text = f"No {relation} are currently decoded for {person.display}."

    evidence = [
        Evidence(kind="relationship", person_id=person.id, person_name=person.display, field=relation, value=label)
        for label in labels
    ]
    return Answer(
        question=question,
        intent=f"person_{relation}",
        answer=answer_text,
        evidence=evidence,
        matched_person_ids=[person.id],
    )


def _birth_fact_answer(tree: ReunionDatabase, question: str, name: str, field: str) -> Answer:
    person, matches = _find_unique_person(tree, name)
    if person is None:
        return _ambiguous_or_missing(question, f"birth_{field}", name, matches)
    birth = _event(person, "birth")
    if birth is None:
        return Answer(question, f"birth_{field}", f"No Birth event is currently decoded for {person.display}.", matched_person_ids=[person.id])

    if field == "date":
        value = birth.date.display if birth.date and birth.date.display else None
        label = "birth date"
    else:
        value = birth.place
        label = "birth place"
    if not value:
        return Answer(question, f"birth_{field}", f"No {label} is currently decoded for {person.display}.", matched_person_ids=[person.id])
    phrase = f"{person.display} was born {'on ' if field == 'date' else 'in '}{value}."
    return Answer(
        question=question,
        intent=f"birth_{field}",
        answer=phrase,
        matched_person_ids=[person.id],
        evidence=[Evidence(kind="event", person_id=person.id, person_name=person.display, event_type="birth", field=field, value=value)],
    )


def _ambiguous_or_missing(question: str, intent: str, name: str, matches: list[Person]) -> Answer:
    if not matches:
        return Answer(question, intent, f"No person matching ‘{_normalise_name(name)}’ was found in the decoded Reunion data.")
    names = ", ".join(f"{item.display} (Person {item.id})" for item in matches)
    return Answer(question, intent, f"The name is ambiguous. Matching people: {names}.", matched_person_ids=[item.id for item in matches], confidence="low")


def _source_answer(tree: ReunionDatabase, question: str, name: str, event_type: str) -> Answer:
    person, matches = _find_unique_person(tree, name)
    if person is None:
        return _ambiguous_or_missing(question, "event_sources", name, matches)
    event = _event(person, event_type)
    if event is None:
        return Answer(question, "event_sources", f"No {event_type.title()} event is currently decoded for {person.display}.", matched_person_ids=[person.id])
    if not event.citations:
        return Answer(question, "event_sources", f"No source citation is currently decoded for {person.display}’s {event_type.title()} event.", matched_person_ids=[person.id])
    descriptions = []
    evidence = []
    for citation in event.citations:
        title = citation.source_title or f"Source {citation.source_id}"
        descriptions.append(title + (f" — {citation.detail}" if citation.detail else ""))
        evidence.append(Evidence(kind="citation", person_id=person.id, person_name=person.display, event_type=event_type, source_id=citation.source_id, source_title=title, citation_detail=citation.detail))
    return Answer(question, "event_sources", f"{person.display}’s {event_type.title()} event is supported by: " + "; ".join(descriptions) + ".", evidence=evidence, matched_person_ids=[person.id])


def _summary_answer(tree: ReunionDatabase, question: str, name: str) -> Answer:
    person, matches = _find_unique_person(tree, name)
    if person is None:
        return _ambiguous_or_missing(question, "person_summary", name, matches)
    parts = [f"{person.display} is stored as Person {person.id}"]
    if person.sex:
        parts.append(f"sex: {person.sex}")
    birth = _event(person, "birth")
    if birth:
        birth_bits = []
        if birth.date and birth.date.display:
            birth_bits.append(birth.date.display)
        if birth.place:
            birth_bits.append(birth.place)
        if birth_bits:
            parts.append("born " + " in ".join(birth_bits))
    if person.spouse_ids:
        parts.append("spouse: " + ", ".join(tree.person_name(item) for item in person.spouse_ids))
    if person.child_ids:
        parts.append("children: " + ", ".join(tree.person_name(item) for item in person.child_ids))
    if person.notes:
        parts.append(f"{len(person.notes)} person note{'s' if len(person.notes) != 1 else ''}")
    if person.media:
        parts.append(f"{len(person.media)} media item{'s' if len(person.media) != 1 else ''}")
    evidence = [Evidence(kind="person", person_id=person.id, person_name=person.display)]
    return Answer(question, "person_summary", "; ".join(parts) + ".", evidence=evidence, matched_person_ids=[person.id], limitations=["This summary includes only fields currently decoded by Reunion Companion."])


def _people_born_in(tree: ReunionDatabase, question: str, place_query: str) -> Answer:
    needle = _normalise_name(place_query).casefold()
    matches: list[tuple[Person, object]] = []
    for person in tree.people.values():
        birth = _event(person, "birth")
        if birth and birth.place and needle in birth.place.casefold():
            matches.append((person, birth))
    if not matches:
        return Answer(question, "people_born_in", f"No decoded Birth events match the place ‘{_normalise_name(place_query)}’.")
    labels = [person.display for person, _birth in matches]
    evidence = [Evidence(kind="event", person_id=person.id, person_name=person.display, event_type="birth", field="place", value=birth.place) for person, birth in matches]
    return Answer(question, "people_born_in", f"{len(labels)} person{'s' if len(labels) != 1 else ''} have decoded Birth events matching {_normalise_name(place_query)}: " + ", ".join(labels) + ".", evidence=evidence, matched_person_ids=[person.id for person, _ in matches])


def _unsourced_births(tree: ReunionDatabase, question: str) -> Answer:
    people = []
    for person in tree.people.values():
        birth = _event(person, "birth")
        if birth is not None and not birth.citations:
            people.append(person)
    if not people:
        return Answer(question, "unsourced_births", "Every currently decoded Birth event has at least one decoded source citation.")
    labels = [person.display for person in people]
    evidence = [Evidence(kind="missing_source", person_id=person.id, person_name=person.display, event_type="birth") for person in people]
    return Answer(question, "unsourced_births", f"{len(people)} person{'s' if len(people) != 1 else ''} have a decoded Birth event with no decoded citation: " + ", ".join(labels) + ".", evidence=evidence, matched_person_ids=[person.id for person in people])


def _media_without_notes(tree: ReunionDatabase, question: str) -> Answer:
    people = [person for person in tree.people.values() if person.media and not person.notes]
    if not people:
        return Answer(question, "media_without_notes", "No decoded people currently have media but no person notes.")
    labels = [person.display for person in people]
    evidence = [Evidence(kind="data_quality", person_id=person.id, person_name=person.display, field="media_without_notes", value=str(len(person.media))) for person in people]
    return Answer(question, "media_without_notes", f"{len(people)} person{'s' if len(people) != 1 else ''} have decoded media but no person note: " + ", ".join(labels) + ".", evidence=evidence, matched_person_ids=[person.id for person in people])



def _generic_event_fact_answer(
    tree: ReunionDatabase,
    question: str,
    name: str,
    event_type: str,
    field: str,
) -> Answer:
    person, matches = _find_unique_person(tree, name)
    if person is None:
        return _ambiguous_or_missing(question, f"event_{field}", name, matches)

    normalised = normalise_event_type(event_type)
    event = _event(person, normalised)
    definition = event_definition(normalised)
    if event is None:
        return Answer(
            question,
            f"event_{field}",
            f"No {definition.label} event is currently decoded for {person.display}.",
            matched_person_ids=[person.id],
            limitations=[
                f"{definition.label} may exist in Reunion but its binary event pattern "
                "may not yet be decoded by Reunion Companion."
            ],
        )

    if field == "date":
        value = event.date.display if event.date and event.date.display else None
        preposition = "on"
    else:
        value = event.place
        preposition = "in"

    if not value:
        return Answer(
            question,
            f"event_{field}",
            f"No {definition.label} {field} is currently decoded for {person.display}.",
            matched_person_ids=[person.id],
        )

    return Answer(
        question,
        f"event_{field}",
        f"{person.display}’s {definition.label} was {preposition} {value}.",
        matched_person_ids=[person.id],
        evidence=[
            Evidence(
                kind="event",
                person_id=person.id,
                person_name=person.display,
                event_type=normalised,
                field=field,
                value=value,
            )
        ],
    )


def ask_tree(tree: ReunionDatabase, question: str) -> Answer:
    cleaned = " ".join(question.strip().split())
    if not cleaned:
        return Answer(question, "unknown", "Please enter a question.", confidence="low")

    for pattern, relation in _RELATION_PATTERNS:
        match = pattern.match(cleaned)
        if match:
            return _relationship_answer(tree, question, match.group(1), relation)

    patterns = (
        (re.compile(r"^(?:when was|what is) (.+?) born\??$", re.I), "date"),
        (re.compile(r"^(?:where was|what is the birthplace of) (.+?)(?: born)?\??$", re.I), "place"),
    )
    for pattern, field in patterns:
        match = pattern.match(cleaned)
        if match:
            return _birth_fact_answer(tree, question, match.group(1), field)


    match = re.match(
        r"^(?:when was|what is the date of) (.+?)(?:'s|’s) "
        r"(death|burial|cremation|baptism|christening|immigration|emigration|probate|divorce)\??$",
        cleaned,
        re.I,
    )
    if match:
        return _generic_event_fact_answer(
            tree, question, match.group(1), match.group(2), "date"
        )

    match = re.match(
        r"^(?:where was|what is the place of) (.+?)(?:'s|’s) "
        r"(death|burial|cremation|baptism|christening|immigration|emigration|probate|divorce)\??$",
        cleaned,
        re.I,
    )
    if match:
        return _generic_event_fact_answer(
            tree, question, match.group(1), match.group(2), "place"
        )

    match = re.match(r"^(?:what sources? (?:support|prove|cite)|show sources? for) (.+?)(?:'s|’s) (birth|death|marriage)\??$", cleaned, re.I)
    if match:
        return _source_answer(tree, question, match.group(1), match.group(2).lower())

    match = re.match(r"^(?:what do you know about|summari[sz]e|tell me everything about) (.+?)\??$", cleaned, re.I)
    if match:
        return _summary_answer(tree, question, match.group(1))

    match = re.match(r"^(?:who|which people) (?:was|were|are) born in (.+?)\??$", cleaned, re.I)
    if match:
        return _people_born_in(tree, question, match.group(1))

    if re.match(r"^(?:who|which people|list (?:all )?people).*(?:no|without).*(?:birth source|source for (?:their )?birth)", cleaned, re.I):
        return _unsourced_births(tree, question)

    if re.match(r"^(?:who|which people|list (?:all )?people).*(?:media|photos?).*(?:no|without).*(?:notes?)", cleaned, re.I):
        return _media_without_notes(tree, question)

    return Answer(
        question=question,
        intent="unknown",
        answer=(
            "I could not map that question to a supported first-pass query. "
            "Try asking about a person’s parents, spouses, children, Birth date/place, Birth sources, "
            "people born in a place, unsourced Birth events, or people with media but no notes."
        ),
        confidence="low",
        limitations=["This first pass is deterministic and does not yet use a language model."],
    )


def ask_package(package_path: str, question: str) -> Answer:
    return ask_tree(load_reunion_database(package_path), question)
