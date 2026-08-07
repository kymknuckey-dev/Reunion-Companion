"""Source-location metadata for objects created from Reunion data."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecordLocation:
    """Physical byte location of decoded data in a Reunion package."""

    offset: int = 0
    length: int = 0

    def __post_init__(self) -> None:
        if isinstance(self.offset, bool) or not isinstance(self.offset, int):
            raise TypeError("RecordLocation offset must be an integer")
        if isinstance(self.length, bool) or not isinstance(self.length, int):
            raise TypeError("RecordLocation length must be an integer")
        if self.offset < 0:
            raise ValueError("RecordLocation offset cannot be negative")
        if self.length < 0:
            raise ValueError("RecordLocation length cannot be negative")

    @property
    def end(self) -> int:
        return self.offset + self.length

    @property
    def is_known(self) -> bool:
        return self.offset != 0 or self.length != 0
