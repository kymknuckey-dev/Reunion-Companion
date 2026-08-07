"""Foundation Layer in-memory genealogy database."""

from __future__ import annotations

from dataclasses import dataclass, field

from .citation import FoundationCitation
from .event import FoundationEvent
from .family import FoundationFamily
from .indexes import FoundationIndexes
from .media import FoundationMedia
from .note import FoundationNote
from .person import FoundationPerson
from .place import FoundationPlace
from .repository import Repository
from .source import FoundationSource


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
    notes: Repository[FoundationNote] = field(default_factory=Repository)
    media: Repository[FoundationMedia] = field(default_factory=Repository)
    sources: Repository[FoundationSource] = field(default_factory=Repository)
    citations: Repository[FoundationCitation] = field(default_factory=Repository)
    indexes: FoundationIndexes = field(default_factory=FoundationIndexes)

    def rebuild_indexes(self) -> None:
        self.indexes.clear()
        for person in self.people:
            self.indexes.index_person(person)
        for place in self.places:
            self.indexes.index_place(place)
        for source in self.sources:
            self.indexes.index_source(source)
        for media in self.media:
            self.indexes.index_media(media)

    def add_person(self, value: FoundationPerson) -> FoundationPerson:
        self.people.add(value)
        self.indexes.index_person(value)
        return value

    def add_family(self, value: FoundationFamily) -> FoundationFamily:
        return self.families.add(value)

    def add_event(self, value: FoundationEvent) -> FoundationEvent:
        return self.events.add(value)

    def add_place(self, value: FoundationPlace) -> FoundationPlace:
        self.places.add(value)
        self.indexes.index_place(value)
        return value

    def add_note(self, value: FoundationNote) -> FoundationNote:
        return self.notes.add(value)

    def add_media(self, value: FoundationMedia) -> FoundationMedia:
        self.media.add(value)
        self.indexes.index_media(value)
        return value

    def add_source(self, value: FoundationSource) -> FoundationSource:
        self.sources.add(value)
        self.indexes.index_source(value)
        return value

    def add_citation(self, value: FoundationCitation) -> FoundationCitation:
        return self.citations.add(value)

    def person(self, object_id: int) -> FoundationPerson:
        return self.people.get(object_id)

    def family(self, object_id: int) -> FoundationFamily:
        return self.families.get(object_id)

    def event(self, object_id: int) -> FoundationEvent:
        return self.events.get(object_id)

    def place(self, object_id: int) -> FoundationPlace:
        return self.places.get(object_id)

    def note(self, object_id: int) -> FoundationNote:
        return self.notes.get(object_id)

    def media_item(self, object_id: int) -> FoundationMedia:
        return self.media.get(object_id)

    def source(self, object_id: int) -> FoundationSource:
        return self.sources.get(object_id)

    def citation(self, object_id: int) -> FoundationCitation:
        return self.citations.get(object_id)

    def find_people_by_name(self, name: str) -> list[FoundationPerson]:
        return [self.people.get(i) for i in self.indexes.person_ids_for_name(name)]

    def find_people_by_surname(self, surname: str) -> list[FoundationPerson]:
        return [self.people.get(i) for i in self.indexes.person_ids_for_surname(surname)]

    def find_places_by_name(self, name: str) -> list[FoundationPlace]:
        return [self.places.get(i) for i in self.indexes.place_ids_for_name(name)]

    def find_sources_by_title(self, title: str) -> list[FoundationSource]:
        return [self.sources.get(i) for i in self.indexes.source_ids_for_title(title)]

    def find_media_by_filename(self, filename: str) -> list[FoundationMedia]:
        return [self.media.get(i) for i in self.indexes.media_ids_for_filename(filename)]

    @property
    def object_counts(self) -> dict[str, int]:
        return {
            "people": len(self.people),
            "families": len(self.families),
            "events": len(self.events),
            "places": len(self.places),
            "notes": len(self.notes),
            "media": len(self.media),
            "sources": len(self.sources),
            "citations": len(self.citations),
        }
