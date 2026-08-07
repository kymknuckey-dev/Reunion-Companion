"""Family object for the additive Foundation Layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .object import FoundationObject

if TYPE_CHECKING:
    from .citation import FoundationCitation
    from .event import FoundationEvent
    from .media import FoundationMedia
    from .note import FoundationNote
    from .person import FoundationPerson


@dataclass(slots=True, kw_only=True)
class FoundationFamily(FoundationObject):
    """A family grouping spouses, children, events, notes, and media."""

    spouses: list["FoundationPerson"] = field(default_factory=list)
    children: list["FoundationPerson"] = field(default_factory=list)
    events: list["FoundationEvent"] = field(default_factory=list)
    notes: list["FoundationNote"] = field(default_factory=list)
    media: list["FoundationMedia"] = field(default_factory=list)
    citations: list["FoundationCitation"] = field(default_factory=list)

    def other_spouses(self, person: "FoundationPerson") -> list["FoundationPerson"]:
        return [spouse for spouse in self.spouses if spouse.id != person.id]

    def add_spouse(self, person: "FoundationPerson") -> None:
        if all(existing.id != person.id for existing in self.spouses):
            self.spouses.append(person)

    def add_child(self, person: "FoundationPerson") -> None:
        if all(existing.id != person.id for existing in self.children):
            self.children.append(person)

    def events_by_type(self, event_type: str) -> list["FoundationEvent"]:
        needle = event_type.casefold()
        return [event for event in self.events if event.event_type.casefold() == needle]
