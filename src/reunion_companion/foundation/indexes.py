"""Simple indexes over Foundation Layer objects."""

from __future__ import annotations

from dataclasses import dataclass, field

from .media import FoundationMedia
from .person import FoundationPerson
from .place import FoundationPlace
from .source import FoundationSource


def _normalise(value: str) -> str:
    return " ".join(value.casefold().split())


@dataclass(slots=True)
class FoundationIndexes:
    """Derived indexes for fast lookup without changing domain objects."""

    people_by_name: dict[str, list[int]] = field(default_factory=dict)
    people_by_surname: dict[str, list[int]] = field(default_factory=dict)
    places_by_name: dict[str, list[int]] = field(default_factory=dict)
    sources_by_title: dict[str, list[int]] = field(default_factory=dict)
    media_by_filename: dict[str, list[int]] = field(default_factory=dict)

    def clear(self) -> None:
        self.people_by_name.clear()
        self.people_by_surname.clear()
        self.places_by_name.clear()
        self.sources_by_title.clear()
        self.media_by_filename.clear()

    def index_person(self, person: FoundationPerson) -> None:
        full_name = _normalise(person.full_name)
        surname = _normalise(person.surname)
        if full_name:
            self.people_by_name.setdefault(full_name, []).append(person.id)
        if surname:
            self.people_by_surname.setdefault(surname, []).append(person.id)

    def index_place(self, place: FoundationPlace) -> None:
        name = _normalise(place.name)
        if name:
            self.places_by_name.setdefault(name, []).append(place.id)

    def index_source(self, source: FoundationSource) -> None:
        title = _normalise(source.title)
        if title:
            self.sources_by_title.setdefault(title, []).append(source.id)

    def index_media(self, media: FoundationMedia) -> None:
        if media.filename:
            filename = _normalise(media.filename)
            self.media_by_filename.setdefault(filename, []).append(media.id)

    def person_ids_for_name(self, name: str) -> list[int]:
        return list(self.people_by_name.get(_normalise(name), ()))

    def person_ids_for_surname(self, surname: str) -> list[int]:
        return list(self.people_by_surname.get(_normalise(surname), ()))

    def place_ids_for_name(self, name: str) -> list[int]:
        return list(self.places_by_name.get(_normalise(name), ()))

    def source_ids_for_title(self, title: str) -> list[int]:
        return list(self.sources_by_title.get(_normalise(title), ()))

    def media_ids_for_filename(self, filename: str) -> list[int]:
        return list(self.media_by_filename.get(_normalise(filename), ()))
