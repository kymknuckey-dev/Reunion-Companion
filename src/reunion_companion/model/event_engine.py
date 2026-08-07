from __future__ import annotations

from dataclasses import dataclass

from .event import Event


@dataclass(slots=True, frozen=True)
class EventTypeDefinition:
    key: str
    label: str
    category: str
    owner_scope: str
    aliases: tuple[str, ...] = ()
    vital: bool = False
    decoder_status: str = "registered"
    note: str | None = None


@dataclass(slots=True)
class EventOccurrence:
    owner_type: str
    owner_id: int
    owner_name: str
    event_index: int
    event: Event
    related_person_ids: list[int]

    @property
    def event_type(self) -> str:
        return self.event.event_type

    @property
    def year(self) -> int | None:
        return self.event.date.year if self.event.date else None
