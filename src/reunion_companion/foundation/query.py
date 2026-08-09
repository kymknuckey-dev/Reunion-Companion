"""Foundation-backed query engine for Reunion Companion Beta 1."""

from __future__ import annotations

from dataclasses import dataclass

from .database import FoundationDatabase
from .event import FoundationEvent
from .media import FoundationMedia
from .person import FoundationPerson
from .place import FoundationPlace
from .source import FoundationSource


def _norm(value: str) -> str:
    return " ".join(value.casefold().split())


@dataclass(slots=True)
class FoundationQueryEngine:
    """Small, deterministic query layer over ``FoundationDatabase``.

    Beta 1 intentionally focuses on high-value, transparent queries rather
    than free-form AI interpretation. Natural-language routing in
    ``console.py`` maps user questions onto these methods.
    """

    database: FoundationDatabase

    def people(
        self,
        text: str = "",
        *,
        surname: str | None = None,
        exact: bool = False,
    ) -> list[FoundationPerson]:
        values = list(self.database.people)
        if surname is not None:
            needle = _norm(surname)
            values = [p for p in values if _norm(p.surname) == needle]

        if text:
            needle = _norm(text)
            if exact:
                values = [p for p in values if _norm(p.full_name) == needle]
            else:
                values = [
                    p for p in values
                    if needle in _norm(p.full_name)
                    or needle in _norm(p.given)
                    or needle in _norm(p.surname)
                ]
        return values

    def person(self, text: str) -> FoundationPerson | None:
        exact = self.people(text, exact=True)
        if len(exact) == 1:
            return exact[0]

        matches = self.people(text)
        if len(matches) == 1:
            return matches[0]
        return None

    def events(
        self,
        *,
        event_type: str | None = None,
        place: str | None = None,
        text: str | None = None,
    ) -> list[FoundationEvent]:
        values = list(self.database.events)

        if event_type:
            needle = _norm(event_type)
            values = [e for e in values if _norm(e.event_type) == needle]

        if place:
            needle = _norm(place)
            values = [
                e for e in values
                if e.display_place and needle in _norm(e.display_place)
            ]

        if text:
            needle = _norm(text)
            values = [
                e for e in values
                if needle in _norm(str(e))
                or (e.memo and needle in _norm(e.memo))
            ]

        return values

    def places(self, text: str = "") -> list[FoundationPlace]:
        values = list(self.database.places)
        if not text:
            return values
        needle = _norm(text)
        return [p for p in values if needle in _norm(p.name)]

    def sources(self, text: str = "") -> list[FoundationSource]:
        values = list(self.database.sources)
        if not text:
            return values
        needle = _norm(text)
        return [s for s in values if needle in _norm(s.title)]

    def media(self, text: str = "") -> list[FoundationMedia]:
        values = list(self.database.media)
        if not text:
            return values
        needle = _norm(text)
        return [
            m for m in values
            if needle in _norm(m.filename or "")
            or needle in _norm(m.caption or "")
            or needle in _norm(m.description or "")
            or needle in _norm(m.media_key)
        ]

    def photos_without_captions(self) -> list[FoundationMedia]:
        return [
            media for media in self.database.media
            if not (media.caption or "").strip()
        ]

    def people_without_birth_source(self) -> list[FoundationPerson]:
        result: list[FoundationPerson] = []
        for person in self.database.people:
            births = person.events_by_type("birth")
            if not births:
                result.append(person)
                continue
            if not any(event.citations for event in births):
                result.append(person)
        return result

    def summary(self) -> dict[str, int]:
        return dict(self.database.object_counts)
