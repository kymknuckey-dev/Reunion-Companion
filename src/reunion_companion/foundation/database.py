"""Foundation Layer in-memory genealogy database."""

from __future__ import annotations

from dataclasses import dataclass, field

from .event import FoundationEvent
from .family import FoundationFamily
from .indexes import FoundationIndexes
from .person import FoundationPerson
from .place import FoundationPlace
from .repository import Repository


@dataclass(slots=True)
class FoundationDatabase:
    """Root container for the future Core Engine object graph."""

    package_path: str | None = None
    version: str | None = None
    warnings: list[str] = field(default_factory=list)

    people: Repository[FoundationPerson] = field(default_factory=Repository)
    families: Repository[FoundationFamily] = field(default_factory=Repository)
    events: Repository[FoundationEvent] = field(default_factory=Repository)
    places: Repository[FoundationPlace] = field(default_factory=Repository)
    indexes: FoundationIndexes = field(default_factory=FoundationIndexes)

    def rebuild_indexes(self) -> None:
        self.indexes.clear()
        for person in self.people:
            self.indexes.index_person(person)
        for place in self.places:
            self.indexes.index_place(place)

    def add_person(self, person: FoundationPerson) -> FoundationPerson:
        self.people.add(person)
        self.indexes.index_person(person)
        return person

    def add_family(self, family: FoundationFamily) -> FoundationFamily:
        return self.families.add(family)

    def add_event(self, event: FoundationEvent) -> FoundationEvent:
        return self.events.add(event)

    def add_place(self, place: FoundationPlace) -> FoundationPlace:
        self.places.add(place)
        self.indexes.index_place(place)
        return place

    def person(self, person_id: int) -> FoundationPerson:
        return self.people.get(person_id)

    def family(self, family_id: int) -> FoundationFamily:
        return self.families.get(family_id)

    def event(self, event_id: int) -> FoundationEvent:
        return self.events.get(event_id)

    def place(self, place_id: int) -> FoundationPlace:
        return self.places.get(place_id)

    def find_people_by_name(self, name: str) -> list[FoundationPerson]:
        return [
            self.people.get(person_id)
            for person_id in self.indexes.person_ids_for_name(name)
        ]

    def find_people_by_surname(self, surname: str) -> list[FoundationPerson]:
        return [
            self.people.get(person_id)
            for person_id in self.indexes.person_ids_for_surname(surname)
        ]

    def find_places_by_name(self, name: str) -> list[FoundationPlace]:
        return [
            self.places.get(place_id)
            for place_id in self.indexes.place_ids_for_name(name)
        ]

    @property
    def object_counts(self) -> dict[str, int]:
        return {
            "people": len(self.people),
            "families": len(self.families),
            "events": len(self.events),
            "places": len(self.places),
        }
