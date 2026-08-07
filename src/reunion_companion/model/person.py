from __future__ import annotations

from dataclasses import dataclass, field

from .event import Event
from .evidence import Evidence
from .media import Media
from .note import Note


@dataclass(slots=True)
class Person:
    id: int
    given: str
    surname: str
    display: str
    sex: str | None
    events: list[Event] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    media: list[Media] = field(default_factory=list)
    parent_family_ids: list[int] = field(default_factory=list)
    spouse_ids: list[int] = field(default_factory=list)
    parent_ids: list[int] = field(default_factory=list)
    child_ids: list[int] = field(default_factory=list)
    attributes: dict[str, object] = field(default_factory=dict)
    flags: set[str] = field(default_factory=set)
    evidence: dict[str, Evidence] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        return self.display
