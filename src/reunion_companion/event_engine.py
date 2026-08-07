from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from typing import Iterable

from .model import EventOccurrence, EventTypeDefinition, ReunionDatabase


EVENT_TYPES: tuple[EventTypeDefinition, ...] = (
    EventTypeDefinition(
        "birth", "Birth", "vital", "person",
        aliases=("born",), vital=True,
        decoder_status="decoded-controlled-probes",
    ),
    EventTypeDefinition(
        "marriage", "Marriage", "family", "family",
        aliases=("married", "wedding"), vital=True,
        decoder_status="decoded-controlled-probes",
    ),
    EventTypeDefinition(
        "death", "Death", "vital", "person",
        aliases=("died",), vital=True,
        note="Registered for the semantic model; a controlled Reunion probe is still required.",
    ),
    EventTypeDefinition(
        "burial", "Burial", "vital", "person",
        aliases=("buried",), vital=True,
        note="Registered; binary field pattern not yet decoded.",
    ),
    EventTypeDefinition(
        "cremation", "Cremation", "vital", "person",
        aliases=("cremated",), vital=True,
        note="Registered; binary field pattern not yet decoded.",
    ),
    EventTypeDefinition(
        "baptism", "Baptism", "religious", "person",
        aliases=("baptised", "baptized"),
        note="Registered; binary field pattern not yet decoded.",
    ),
    EventTypeDefinition(
        "christening", "Christening", "religious", "person",
        aliases=("christened",),
        note="Registered; binary field pattern not yet decoded.",
    ),
    EventTypeDefinition(
        "occupation", "Occupation", "life", "person",
        aliases=("worked", "employment"),
        note="Registered; binary field pattern not yet decoded.",
    ),
    EventTypeDefinition(
        "residence", "Residence", "life", "person",
        aliases=("lived", "address"),
        note="Registered; binary field pattern not yet decoded.",
    ),
    EventTypeDefinition(
        "census", "Census", "life", "person",
        aliases=("enumeration",),
        note="Registered; binary field pattern not yet decoded.",
    ),
    EventTypeDefinition(
        "immigration", "Immigration", "migration", "person",
        aliases=("immigrated", "arrival"),
        note="Registered; binary field pattern not yet decoded.",
    ),
    EventTypeDefinition(
        "emigration", "Emigration", "migration", "person",
        aliases=("emigrated", "departure"),
        note="Registered; binary field pattern not yet decoded.",
    ),
    EventTypeDefinition(
        "military_service", "Military Service", "service", "person",
        aliases=("military", "war service", "served"),
        note="Registered; binary field pattern not yet decoded.",
    ),
    EventTypeDefinition(
        "education", "Education", "life", "person",
        aliases=("school", "university"),
        note="Registered; binary field pattern not yet decoded.",
    ),
    EventTypeDefinition(
        "probate", "Probate", "legal", "person",
        aliases=("will",),
        note="Registered; binary field pattern not yet decoded.",
    ),
    EventTypeDefinition(
        "divorce", "Divorce", "family", "family",
        aliases=("divorced",),
        note="Registered; binary field pattern not yet decoded.",
    ),
    EventTypeDefinition(
        "custom", "Custom Event", "custom", "either",
        aliases=("custom event",),
        note="Registered; custom event labels and field identifiers require probes.",
    ),
)

_EVENT_BY_KEY = {definition.key: definition for definition in EVENT_TYPES}
_EVENT_ALIASES = {
    alias.casefold(): definition.key
    for definition in EVENT_TYPES
    for alias in (definition.key, definition.label, *definition.aliases)
}


def normalise_event_type(value: str) -> str:
    cleaned = " ".join(value.strip().replace("-", " ").replace("_", " ").split()).casefold()
    return _EVENT_ALIASES.get(cleaned, cleaned.replace(" ", "_"))


def event_definition(event_type: str) -> EventTypeDefinition:
    key = normalise_event_type(event_type)
    return _EVENT_BY_KEY.get(
        key,
        EventTypeDefinition(
            key=key,
            label=key.replace("_", " ").title(),
            category="unknown",
            owner_scope="either",
            decoder_status="observed-unregistered",
            note="This event type was present in the semantic model but is not in the registry.",
        ),
    )


def event_sort_key(occurrence: EventOccurrence) -> tuple[int, int, int, str, int]:
    date = occurrence.event.date
    if date is None:
        return (9999, 13, 32, occurrence.event_type, occurrence.event_index)
    return (
        date.year,
        date.month if date.month is not None else 13,
        date.day if date.day is not None else 32,
        occurrence.event_type,
        occurrence.event_index,
    )


class EventEngine:
    """Search, timeline and audit operations over generic semantic Events."""

    def __init__(self, database: ReunionDatabase):
        self.database = database

    def all_events(self) -> list[EventOccurrence]:
        occurrences: list[EventOccurrence] = []

        for person_id, person in self.database.people.items():
            for index, event in enumerate(person.events):
                occurrences.append(
                    EventOccurrence(
                        owner_type="person",
                        owner_id=person_id,
                        owner_name=person.display,
                        event_index=index,
                        event=event,
                        related_person_ids=[person_id],
                    )
                )

        for family_id, family in self.database.families.items():
            related = list(dict.fromkeys([*family.spouse_ids, *family.child_ids]))
            spouse_names = [
                self.database.person_name(person_id)
                for person_id in family.spouse_ids
            ]
            owner_name = (
                " and ".join(spouse_names)
                if spouse_names
                else f"Family {family_id}"
            )
            for index, event in enumerate(family.events):
                occurrences.append(
                    EventOccurrence(
                        owner_type="family",
                        owner_id=family_id,
                        owner_name=owner_name,
                        event_index=index,
                        event=event,
                        related_person_ids=related,
                    )
                )

        return sorted(occurrences, key=event_sort_key)

    def search(
        self,
        *,
        event_type: str | None = None,
        person_id: int | None = None,
        place: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        sourced: bool | None = None,
        owner_type: str | None = None,
    ) -> list[EventOccurrence]:
        target_type = normalise_event_type(event_type) if event_type else None
        place_needle = place.casefold().strip() if place else None

        matches: list[EventOccurrence] = []
        for occurrence in self.all_events():
            event = occurrence.event

            if target_type and normalise_event_type(event.event_type) != target_type:
                continue
            if person_id is not None and person_id not in occurrence.related_person_ids:
                continue
            if owner_type and occurrence.owner_type != owner_type:
                continue
            if place_needle and place_needle not in (event.place or "").casefold():
                continue

            year = occurrence.year
            if year_from is not None and (year is None or year < year_from):
                continue
            if year_to is not None and (year is None or year > year_to):
                continue

            has_sources = bool(event.citations)
            if sourced is not None and has_sources != sourced:
                continue

            matches.append(occurrence)

        return matches

    def timeline(
        self,
        person_id: int,
        *,
        include_family_events: bool = True,
    ) -> list[EventOccurrence]:
        self.database.get_person(person_id)
        occurrences = self.search(person_id=person_id)

        if not include_family_events:
            occurrences = [
                item
                for item in occurrences
                if item.owner_type == "person"
            ]
        else:
            # A family event belongs in a person's own life timeline only when
            # that person is a spouse in the family. A parent's marriage is not
            # silently presented as the child's personal event.
            spouse_family_ids = {
                family.id
                for family in self.database.families.values()
                if person_id in family.spouse_ids
            }
            occurrences = [
                item
                for item in occurrences
                if item.owner_type == "person"
                or item.owner_id in spouse_family_ids
            ]

        return sorted(occurrences, key=event_sort_key)

    def type_counts(self) -> dict[str, int]:
        counts = Counter(
            normalise_event_type(item.event_type)
            for item in self.all_events()
        )
        return dict(sorted(counts.items()))

    def unsourced(self, event_type: str | None = None) -> list[EventOccurrence]:
        return self.search(event_type=event_type, sourced=False)

    def registry_status(self) -> list[dict[str, object]]:
        counts = self.type_counts()
        result: list[dict[str, object]] = []
        registered_keys = set()

        for definition in EVENT_TYPES:
            registered_keys.add(definition.key)
            result.append({
                **asdict(definition),
                "decoded_count": counts.get(definition.key, 0),
            })

        for key, count in counts.items():
            if key in registered_keys:
                continue
            definition = event_definition(key)
            result.append({
                **asdict(definition),
                "decoded_count": count,
            })

        return result

    def summary(self) -> dict[str, object]:
        events = self.all_events()
        dated = sum(item.event.date is not None for item in events)
        placed = sum(bool(item.event.place) for item in events)
        sourced = sum(bool(item.event.citations) for item in events)
        return {
            "total_events": len(events),
            "person_events": sum(item.owner_type == "person" for item in events),
            "family_events": sum(item.owner_type == "family" for item in events),
            "dated_events": dated,
            "placed_events": placed,
            "sourced_events": sourced,
            "unsourced_events": len(events) - sourced,
            "types": self.type_counts(),
        }
