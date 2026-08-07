"""Media object for the additive Foundation Layer."""

from __future__ import annotations

from dataclasses import dataclass

from .object import FoundationObject


@dataclass(slots=True, kw_only=True)
class FoundationMedia(FoundationObject):
    """A media attachment represented independently of Reunion storage."""

    media_key: str
    owner_type: str
    owner_id: int
    fingerprint: str
    filename: str | None = None
    original_path: str | None = None
    media_type: str | None = None
    caption: str | None = None
    description: str | None = None
    filename_link_status: str | None = None
    metadata_link_status: str | None = None

    @property
    def display_name(self) -> str:
        return self.filename or self.caption or self.media_key

    @property
    def has_metadata(self) -> bool:
        return bool(self.caption or self.description)

    def __str__(self) -> str:
        return self.display_name
