"""
Person model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .base import ReunionObject, Sex

if TYPE_CHECKING:
    from .citation import Citation
    from .event import Event
    from .family import Family
    from .media import Media
    from .note import Note


@dataclass(slots=True)
class Person(ReunionObject):
    """
    Represents one person in the Reunion database.
    """

    given: str = ""
    surname: str = ""

    sex: Sex = Sex.UNKNOWN

    birth: Event | None = None
    death: Event | None = None

    parent_families: list["Family"] = field(default_factory=list)
    spouse_families: list["Family"] = field(default_factory=list)

    events: list["Event"] = field(default_factory=list)
    notes: list["Note"] = field(default_factory=list)
    media: list["Media"] = field(default_factory=list)
    citations: list["Citation"] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        if self.given and self.surname:
            return f"{self.given} {self.surname}"

        if self.given:
            return self.given

        if self.surname:
            return self.surname

        return "(Unnamed Person)"

    @property
    def parents(self) -> list["Person"]:
        result: list[Person] = []

        for family in self.parent_families:
            result.extend(family.parents)

        return result

    @property
    def spouses(self) -> list["Person"]:
        result: list[Person] = []

        for family in self.spouse_families:
            spouse = family.other_spouse(self)

            if spouse is not None:
                result.append(spouse)

        return result

    @property
    def children(self) -> list["Person"]:
        result: list[Person] = []

        for family in self.spouse_families:
            result.extend(family.children)

        return result

    def add_event(self, event: "Event") -> None:
        self.events.append(event)

    def add_note(self, note: "Note") -> None:
        self.notes.append(note)

    def add_media(self, media: "Media") -> None:
        self.media.append(media)

    def add_citation(self, citation: "Citation") -> None:
        self.citations.append(citation)

    def __str__(self) -> str:
        return self.full_name