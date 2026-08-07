from __future__ import annotations

from dataclasses import dataclass, field

from .evidence import Evidence


@dataclass(slots=True)
class ReunionDate:
    raw_value: int
    day: int | None
    month: int | None
    year: int
    year_code: int
    high_flags: int
    qualifier: int | None = None
    qualifier_name: str | None = None
    display: str | None = None
    evidence: Evidence = field(default_factory=Evidence)


@dataclass(slots=True)
class Citation:
    source_id: int
    detail: str | None = None
    source_title: str | None = None
    raw_offset: int | None = None
    decode_status: str = "decoded-controlled-probes"
    evidence: Evidence = field(default_factory=Evidence)


@dataclass(slots=True)
class Event:
    event_type: str
    date: ReunionDate | None = None
    place_id: int | None = None
    place: str | None = None
    memo: str | None = None
    citations: list[Citation] = field(default_factory=list)
    raw_offset: int | None = None
    decode_status: str = "experimental"
    media_ids: list[str] = field(default_factory=list)
    evidence: dict[str, Evidence] = field(default_factory=dict)

    @property
    def type(self) -> str:
        """Stable semantic alias for callers that prefer `event.type`."""
        return self.event_type
