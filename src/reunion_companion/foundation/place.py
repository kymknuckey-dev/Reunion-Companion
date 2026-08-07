"""Place object for the additive Foundation Layer."""

from __future__ import annotations

from dataclasses import dataclass

from .object import FoundationObject


@dataclass(slots=True, kw_only=True)
class FoundationPlace(FoundationObject):
    """A named genealogy place.

    Coordinates are optional because Reunion Companion has not yet decoded
    coordinate storage from controlled Reunion 14 probes.
    """

    name: str = ""
    latitude: float | None = None
    longitude: float | None = None

    @property
    def has_coordinates(self) -> bool:
        """Whether both latitude and longitude are known."""
        return self.latitude is not None and self.longitude is not None

    def __str__(self) -> str:
        return self.name or f"Place {self.id}"
