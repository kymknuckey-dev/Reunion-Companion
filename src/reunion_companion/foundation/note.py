"""Note object for the additive Foundation Layer."""

from __future__ import annotations

from dataclasses import dataclass

from .object import FoundationObject


@dataclass(slots=True, kw_only=True)
class FoundationNote(FoundationObject):
    """A decoded note attached to a genealogy owner."""

    note_type: str
    text: str
    format: str = "plain"
    owner_type: str | None = None
    owner_id: int | None = None
    source_offset: int | None = None
    decode_status: str | None = None

    @property
    def is_empty(self) -> bool:
        return not self.text.strip()

    def __str__(self) -> str:
        return self.text
