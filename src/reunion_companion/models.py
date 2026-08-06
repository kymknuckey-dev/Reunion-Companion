from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ReunionDate:
    raw_value: int
    day: int | None
    month: int | None
    year: int
    year_code: int
    high_flags: int
    qualifier: int | None = None
    qualifier_name: str | None = None
    display: str | None = None


@dataclass(slots=True)
class Note:
    note_type: str
    text: str
    format: str = "plain"
    raw_offset: int | None = None
    decode_status: str = "decoded-controlled-probes"


@dataclass(slots=True)
class Source:
    source_id: int
    title: str
    source_type: str = "free-form"
    raw_offset: int | None = None
    decode_status: str = "decoded-controlled-probes"


@dataclass(slots=True)
class Citation:
    source_id: int
    detail: str | None = None
    source_title: str | None = None
    raw_offset: int | None = None
    decode_status: str = "decoded-controlled-probes"


@dataclass(slots=True)
class Event:
    event_type: str
    date: ReunionDate | None = None
    place_id: int | None = None
    place: str | None = None
    memo: str | None = None
    citations: list[Citation] = field(default_factory=list)
    raw_offset: int | None = None
    decode_status: str = "experimental"


@dataclass(slots=True)
class Person:
    record_id: int | None
    given: str
    surname: str
    sex: str | None = None
    events: list[Event] = field(default_factory=list)
    raw_offset: int | None = None


@dataclass(slots=True)
class Family:
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
