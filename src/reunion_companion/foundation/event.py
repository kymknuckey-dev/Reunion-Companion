"""Event object for the additive Foundation Layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .object import FoundationObject

if TYPE_CHECKING:
    from .place import FoundationPlace


@dataclass(slots=True, kw_only=True)
class FoundationEvent(FoundationObject):
    """A generic genealogy event in the future Core Engine graph."""

    event_type: str
    date_text: str | None = None
    place: "FoundationPlace | None" = None
    memo: str | None = None
    owner_type: str | None = None
    owner_id: int | None = None

    @property
    def has_date(self) -> bool:
        return bool(self.date_text)

    @property
    def has_place(self) -> bool:
        return self.place is not None

    @property
    def label(self) -> str:
        """Human-readable event type."""
        cleaned = self.event_type.replace("_", " ").strip()
        return cleaned.title() if cleaned else "Event"

    def __str__(self) -> str:
        details: list[str] = [self.label]
        if self.date_text:
            details.append(self.date_text)
        if self.place is not None and self.place.name:
            details.append(self.place.name)
        return " — ".join(details)
