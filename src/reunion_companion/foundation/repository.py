"""Generic repositories for Foundation Layer objects."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Generic, TypeVar

from .ids import ObjectId
from .object import FoundationObject

T = TypeVar("T", bound=FoundationObject)


class DuplicateObjectError(ValueError):
    """Raised when a repository already contains an object's identifier."""


class ObjectNotFoundError(KeyError):
    """Raised when an object identifier is not present in a repository."""


class Repository(Generic[T]):
    """Ordered in-memory repository keyed by stable object identifier.

    Repositories intentionally hide the underlying dictionary so future
    storage backends can preserve the same application-facing API.
    """

    def __init__(self, values: Iterable[T] = ()) -> None:
        self._objects: dict[int, T] = {}
        for value in values:
            self.add(value)

    def add(self, value: T, *, replace: bool = False) -> T:
        """Add ``value`` and return it.

        By default duplicate identifiers are rejected. ``replace=True`` is
        reserved for controlled builder/update workflows.
        """
        object_id = value.id
        if object_id in self._objects and not replace:
            raise DuplicateObjectError(
                f"{value.object_type} {object_id} already exists"
            )
        self._objects[object_id] = value
        return value

    def get(self, object_id: int | ObjectId) -> T:
        """Return an object or raise ``ObjectNotFoundError``."""
        key = int(ObjectId.coerce(object_id))
        try:
            return self._objects[key]
        except KeyError as exc:
            raise ObjectNotFoundError(f"Object {key} was not found") from exc

    def find(self, object_id: int | ObjectId) -> T | None:
        """Return an object if present, otherwise ``None``."""
        key = int(ObjectId.coerce(object_id))
        return self._objects.get(key)

    def remove(self, object_id: int | ObjectId) -> T:
        """Remove and return an object."""
        key = int(ObjectId.coerce(object_id))
        try:
            return self._objects.pop(key)
        except KeyError as exc:
            raise ObjectNotFoundError(f"Object {key} was not found") from exc

    def clear(self) -> None:
        """Remove all objects."""
        self._objects.clear()

    def all(self) -> list[T]:
        """Return objects in insertion order."""
        return list(self._objects.values())

    def ids(self) -> list[int]:
        """Return identifiers in insertion order."""
        return list(self._objects.keys())

    @property
    def count(self) -> int:
        return len(self._objects)

    @property
    def is_empty(self) -> bool:
        return not self._objects

    def __contains__(self, object_id: object) -> bool:
        if isinstance(object_id, ObjectId):
            return int(object_id) in self._objects
        if isinstance(object_id, int) and not isinstance(object_id, bool):
            return object_id in self._objects
        return False

    def __iter__(self) -> Iterator[T]:
        return iter(self._objects.values())

    def __len__(self) -> int:
        return len(self._objects)
