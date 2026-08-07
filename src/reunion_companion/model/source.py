from __future__ import annotations

from dataclasses import dataclass, field

from .evidence import Evidence


@dataclass(slots=True)
class Source:
    source_id: int
    title: str
    source_type: str = "free-form"
    raw_offset: int | None = None
    decode_status: str = "decoded-controlled-probes"
    repository_id: int | None = None
    evidence: Evidence = field(default_factory=Evidence)

    @property
    def id(self) -> int:
        return self.source_id
