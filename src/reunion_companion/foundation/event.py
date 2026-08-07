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
    place_text: str | None = None
    memo: str | None = None
    owner_type: str | None = None
    owner_id: int | None = None
    source_offset: int | None = None
    decode_status: str | None = None

    @property
    def has_date(self) -> bool:
        return bool(self.date_text)

    @property
    def has_place(self) -> bool:
        return self.place is not None or bool(self.place_text)

    @property
    def label(self) -> str:
        cleaned = self.event_type.replace("_", " ").strip()
        return cleaned.title() if cleaned else "Event"

    @property
    def display_place(self) -> str | None:
        if self.place is not None and self.place.name:
            return self.place.name
        return self.place_text

    def __str__(self) -> str:
        details: list[str] = [self.label]
        if self.date_text:
            details.append(self.date_text)
        if self.display_place:
            details.append(self.display_place)
        return " — ".join(details)
