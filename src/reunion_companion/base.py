"""
Core model base classes.

These classes define the object model used throughout Reunion Companion.
The model layer is deliberately independent of the Reunion binary format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Sex(Enum):
    """Person sex."""

    UNKNOWN = 0
    MALE = 1
    FEMALE = 2

    @classmethod
    def from_code(cls, value: int) -> "Sex":
        return {
            1: cls.MALE,
            2: cls.FEMALE,
        }.get(value, cls.UNKNOWN)


@dataclass(slots=True, frozen=True)
class RecordLocation:
    """
    Physical location of an object inside the Reunion package.

    Used for diagnostics and future editing support.
    """

    offset: int = 0
    length: int = 0


@dataclass(slots=True)
class ReunionObject:
    """
    Base class for every genealogy object.
    """

    id: int

    location: RecordLocation = field(default_factory=RecordLocation)

    modified: bool = False

    tags: dict[str, Any] = field(default_factory=dict)

    @property
    def object_type(self) -> str:
        return self.__class__.__name__

    @property
    def identity(self) -> str:
        return f"{self.object_type}({self.id})"

    def mark_modified(self) -> None:
        self.modified = True

    def __repr__(self) -> str:
        return self.identity