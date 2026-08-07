"""Citation object for the additive Foundation Layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .object import FoundationObject

if TYPE_CHECKING:
    from .source import FoundationSource


@dataclass(slots=True, kw_only=True)
class FoundationCitation(FoundationObject):
    """A citation connecting an event to a source."""

    source: "FoundationSource | None" = None
    source_id: int | None = None
    source_title: str | None = None
    detail: str | None = None
    owner_type: str | None = None
    owner_id: int | None = None
    event_id: int | None = None
    source_offset: int | None = None
    decode_status: str | None = None

    @property
    def resolved(self) -> bool:
        return self.source is not None

    @property
    def display_source(self) -> str:
        if self.source is not None:
            return self.source.title
        if self.source_title:
            return self.source_title
        if self.source_id is not None:
            return f"Source {self.source_id}"
        return "Unknown source"
