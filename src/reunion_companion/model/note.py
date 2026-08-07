from __future__ import annotations

from dataclasses import dataclass, field

from .evidence import Evidence


@dataclass(slots=True)
class Note:
    note_type: str
    text: str
    format: str = "plain"
    raw_offset: int | None = None
    decode_status: str = "decoded-controlled-probes"
    evidence: Evidence = field(default_factory=Evidence)
