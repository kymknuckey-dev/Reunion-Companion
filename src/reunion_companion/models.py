"""Compatibility exports for the v0.6 semantic model.

New code should import from ``reunion_companion.model``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .model import Citation, Event, Note, ReunionDate, Source


@dataclass(slots=True)
class Person:
    """Low-level compatibility record used by early parser tests."""

    record_id: int | None
    given: str
    surname: str
    sex: str | None = None
    events: list[Event] = field(default_factory=list)
    raw_offset: int | None = None


@dataclass(slots=True)
class Family:
    """Low-level compatibility record used by early parser tests."""

    record_id: int | None
    spouse_ids: list[int] = field(default_factory=list)
    child_ids: list[int] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)


@dataclass(slots=True)
class ReunionPackage:
    package_path: Path
    version: str
    main_data_path: Path
    main_data_size: int


__all__ = [
    "Citation",
    "Event",
    "Family",
    "Note",
    "Person",
    "ReunionDate",
    "ReunionPackage",
    "Source",
]
