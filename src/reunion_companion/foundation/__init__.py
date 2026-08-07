"""Experimental Foundation Layer for Reunion Companion v0.10."""

from .adapters import from_package, from_semantic_database
from .builder import FoundationBuilder, FoundationBuildReport
from .database import FoundationDatabase
from .event import FoundationEvent
from .family import FoundationFamily
from .ids import ObjectId
from .indexes import FoundationIndexes
from .location import RecordLocation
from .object import FoundationObject
from .person import FoundationPerson
from .place import FoundationPlace
from .repository import (
    DuplicateObjectError,
    ObjectNotFoundError,
    Repository,
)

__all__ = [
    "DuplicateObjectError",
    "FoundationBuildReport",
    "FoundationBuilder",
    "FoundationDatabase",
    "FoundationEvent",
    "FoundationFamily",
    "FoundationIndexes",
    "FoundationObject",
    "FoundationPerson",
    "FoundationPlace",
    "ObjectId",
    "ObjectNotFoundError",
    "RecordLocation",
    "Repository",
    "from_package",
    "from_semantic_database",
]
