"""Source object for the additive Foundation Layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .object import FoundationObject

if TYPE_CHECKING:
    from .citation import FoundationCitation


@dataclass(slots=True, kw_only=True)
class FoundationSource(FoundationObject):
    """A genealogy source and the citations that refer to it."""

    title: str
    source_type: str = "free-form"
    repository_id: int | None = None
    source_offset: int | None = None
    decode_status: str | None = None
    citations: list["FoundationCitation"] = field(default_factory=list)

    def __str__(self) -> str:
        return self.title
