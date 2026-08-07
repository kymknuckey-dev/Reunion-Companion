from __future__ import annotations

from dataclasses import dataclass, field

from .evidence import Evidence
from .media import Media
from .note import Note


@dataclass(slots=True)
class Place:
    id: int
    name: str
    latitude: float | None = None
    longitude: float | None = None
    notes: list[Note] = field(default_factory=list)
    media: list[Media] = field(default_factory=list)
    evidence: Evidence = field(default_factory=Evidence)
