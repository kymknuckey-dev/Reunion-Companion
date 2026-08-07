from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Iterable

from .event import Event
from .family import Family
from .media import Media
from .person import Person
from .place import Place
from .source import Source


@dataclass(slots=True)
class ReunionDatabase:
    """Stable semantic API for one read-only Reunion family file."""

    package_path: str
    version: str
    people: dict[int, Person]
    families: dict[int, Family]
    warnings: list[str]
    sources: dict[int, Source] = field(default_factory=dict)
    places: dict[int, Place] = field(default_factory=dict)
    media: dict[str, Media] = field(default_factory=dict)
    repositories: dict[int, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "package_path": self.package_path,
            "version": self.version,
            "people": {
                str(person_id): asdict(person)
                for person_id, person in sorted(self.people.items())
            },
            "families": {
                str(family_id): asdict(family)
                for family_id, family in sorted(self.families.items())
            },
            "sources": {
                str(source_id): asdict(source)
                for source_id, source in sorted(self.sources.items())
            },
            "places": {
                str(place_id): asdict(place)
                for place_id, place in sorted(self.places.items())
            },
            "media": {
                media_key: asdict(item)
                for media_key, item in sorted(self.media.items())
            },
            "warnings": list(self.warnings),
        }

    def get_person(self, person_id: int) -> Person:
        try:
            return self.people[person_id]
        except KeyError as exc:
            raise KeyError(f"Person {person_id} was not found") from exc

    def get_family(self, family_id: int) -> Family:
        try:
            return self.families[family_id]
        except KeyError as exc:
            raise KeyError(f"Family {family_id} was not found") from exc

    def find_people(self, query: str) -> list[Person]:
        needle = query.casefold().strip()
        if not needle:
            return []
        return [
            person
            for person in self.people.values()
            if needle in person.display.casefold()
            or needle in person.given.casefold()
            or needle in person.surname.casefold()
        ]

    def find_events(
        self,
        event_type: str | None = None,
        place: str | None = None,
    ) -> list[tuple[int, Event]]:
        type_needle = event_type.casefold() if event_type else None
        place_needle = place.casefold() if place else None
        matches: list[tuple[int, Event]] = []
        for person_id, person in self.people.items():
            for event in person.events:
                if type_needle and event.event_type.casefold() != type_needle:
                    continue
                if place_needle and place_needle not in (event.place or "").casefold():
                    continue
                matches.append((person_id, event))
        return matches

    def person_name(self, person_id: int) -> str:
        person = self.people.get(person_id)
        return person.display if person else f"Person {person_id}"

    def summary(self) -> dict[str, int]:
        return {
            "people": len(self.people),
            "families": len(self.families),
            "sources": len(self.sources),
            "places": len(self.places),
            "media": len(self.media),
            "person_events": sum(len(person.events) for person in self.people.values()),
            "family_events": sum(len(family.events) for family in self.families.values()),
            "notes": sum(len(person.notes) for person in self.people.values()),
            "citations": sum(
                len(event.citations)
                for person in self.people.values()
                for event in person.events
            ),
        }


# Historical name retained for third-party callers and existing CLI code.
GenealogyTree = ReunionDatabase
