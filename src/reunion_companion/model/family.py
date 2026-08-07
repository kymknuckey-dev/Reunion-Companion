from __future__ import annotations

from dataclasses import dataclass, field

from .event import Event
from .evidence import Evidence
from .media import Media
from .note import Note


@dataclass(slots=True)
class Family:
    id: int
    spouse_ids: list[int] = field(default_factory=list)
    child_ids: list[int] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    media: list[Media] = field(default_factory=list)
    evidence: dict[str, Evidence] = field(default_factory=dict)
