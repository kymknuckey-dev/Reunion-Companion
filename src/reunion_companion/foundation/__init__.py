"""Foundation Layer for Reunion Companion v0.10 Beta 1."""

from .adapters import from_package, from_semantic_database
from .builder import FoundationBuilder, FoundationBuildReport
from .citation import FoundationCitation
from .database import FoundationDatabase
from .diagnostics import DiagnosticReport, DiagnosticSection, FoundationDiagnostics
from .diagnostic_formatter import format_diagnostic_report, format_diagnostic_section
from .event import FoundationEvent
from .family import FoundationFamily
from .formatter import format_counts, format_person
from .ids import ObjectId
from .indexes import FoundationIndexes
from .location import RecordLocation
from .media import FoundationMedia
from .note import FoundationNote
from .object import FoundationObject
from .person import FoundationPerson
from .place import FoundationPlace
from .query import FoundationQueryEngine
from .repository import DuplicateObjectError, ObjectNotFoundError, Repository
from .source import FoundationSource

__all__ = [
    "DuplicateObjectError",
    "FoundationBuildReport",
    "FoundationBuilder",
    "FoundationCitation",
    "DiagnosticReport",
    "DiagnosticSection",
    "FoundationDatabase",
    "FoundationDiagnostics",
    "FoundationEvent",
    "FoundationFamily",
    "FoundationIndexes",
    "FoundationMedia",
    "FoundationNote",
    "FoundationObject",
    "FoundationPerson",
    "FoundationPlace",
    "FoundationQueryEngine",
    "FoundationSource",
    "ObjectId",
    "ObjectNotFoundError",
    "RecordLocation",
    "Repository",
    "format_counts",
    "format_diagnostic_report",
    "format_diagnostic_section",
    "format_person",
    "from_package",
    "from_semantic_database",
]
