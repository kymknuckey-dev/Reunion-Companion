"""Base object contract for the Reunion Companion foundation layer."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .ids import ObjectId
from .location import RecordLocation


@dataclass(slots=True, kw_only=True)
class FoundationObject:
    """Base class for objects produced by the future Core Engine builder."""

    object_id: ObjectId
    location: RecordLocation = field(default_factory=RecordLocation)
    modified: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.object_id = ObjectId.coerce(self.object_id)

    @property
    def id(self) -> int:
        return int(self.object_id)

    @property
    def object_type(self) -> str:
        return type(self).__name__

    @property
    def identity(self) -> str:
        return f"{self.object_type}({self.id})"

    def mark_modified(self) -> None:
        self.modified = True

    def clear_modified(self) -> None:
        self.modified = False
