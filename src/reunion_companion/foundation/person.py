"""Person object for the additive Foundation Layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .object import FoundationObject

if TYPE_CHECKING:
    from .citation import FoundationCitation
    from .event import FoundationEvent
    from .family import FoundationFamily
    from .media import FoundationMedia
    from .note import FoundationNote


@dataclass(slots=True, kw_only=True)
class FoundationPerson(FoundationObject):
    """A person in the future Core Engine object graph."""

    given: str = ""
    surname: str = ""
    display_name: str | None = None
    sex: str = "unknown"

    parent_families: list["FoundationFamily"] = field(default_factory=list)
    spouse_families: list["FoundationFamily"] = field(default_factory=list)
    events: list["FoundationEvent"] = field(default_factory=list)
    notes: list["FoundationNote"] = field(default_factory=list)
    media: list["FoundationMedia"] = field(default_factory=list)
    citations: list["FoundationCitation"] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        if self.display_name:
            return self.display_name
        name = " ".join(part for part in (self.given, self.surname) if part).strip()
        return name or "(Unnamed Person)"

    @property
    def parents(self) -> list["FoundationPerson"]:
        result: list[FoundationPerson] = []
        seen: set[int] = set()
        for family in self.parent_families:
            for parent in family.spouses:
                if parent.id == self.id or parent.id in seen:
                    continue
                seen.add(parent.id)
                result.append(parent)
        return result

    @property
    def spouses(self) -> list["FoundationPerson"]:
        result: list[FoundationPerson] = []
        seen: set[int] = set()
        for family in self.spouse_families:
            for spouse in family.spouses:
                if spouse.id == self.id or spouse.id in seen:
                    continue
                seen.add(spouse.id)
                result.append(spouse)
        return result

    @property
    def children(self) -> list["FoundationPerson"]:
        result: list[FoundationPerson] = []
        seen: set[int] = set()
        for family in self.spouse_families:
            for child in family.children:
                if child.id in seen:
                    continue
                seen.add(child.id)
                result.append(child)
        return result

    def events_by_type(self, event_type: str) -> list["FoundationEvent"]:
        needle = event_type.casefold()
        return [event for event in self.events if event.event_type.casefold() == needle]

    def __str__(self) -> str:
        return self.full_name
