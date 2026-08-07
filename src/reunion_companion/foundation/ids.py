"""Stable identifiers for the Reunion Companion foundation layer."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True, slots=True)
class ObjectId:
    """Typed integer identity for a foundation object."""

    value: int

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not isinstance(self.value, int):
            raise TypeError("ObjectId value must be an integer")
        if self.value < 0:
            raise ValueError("ObjectId value cannot be negative")

    @classmethod
    def coerce(cls, value: int | "ObjectId") -> "ObjectId":
        """Return ``value`` as an ``ObjectId``."""
        if isinstance(value, cls):
            return value
        return cls(value)

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)
