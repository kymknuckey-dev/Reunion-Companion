from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import re

from .caches import CacheSummary, build_cache_summary
from .parser import BinaryReader

_PRINTABLE = set(range(32, 127)) | {9, 10, 13}
_MEDIA_SUFFIXES = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".pdf", ".mov", ".mp4")


@dataclass(slots=True)
class FileInventory:
    name: str
    relative_path: str
    size: int
    category: str


@dataclass(slots=True)
class PersonCandidate:
    offset: int
    given: str
    surname: str
    display: str


@dataclass(slots=True)
class ThumbnailInventory:
    total: int = 0
    person: int = 0
    family: int = 0
    unknown: int = 0


@dataclass(slots=True)
class PackageInventory:
    package_path: str
    version: str
    main_data_path: str
    main_data_size: int
    total_files: int
    total_package_size: int
    files: list[FileInventory] = field(default_factory=list)
    people: list[PersonCandidate] = field(default_factory=list)
    person_tags: int = 0
    media_strings: int = 0
    path_strings: int = 0
    thumbnails: ThumbnailInventory = field(default_factory=ThumbnailInventory)
    caches: CacheSummary = field(default_factory=CacheSummary)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _category(path: Path, main_data_path: Path) -> str:
    if path == main_data_path:
        return "main-data"
    if path.suffix == ".cache":
        return "cache"
    if path.name == "familyfile.signature":
        return "signature"
    if "thumbnails" in path.parts:
        return "thumbnail"
    return "other"


def _ascii_runs(data: bytes, minimum: int = 5) -> list[tuple[int, str]]:
    runs: list[tuple[int, str]] = []
    start: int | None = None

    for index, value in enumerate(data + b"\0"):
        if value in _PRINTABLE:
            if start is None:
                start = index
        elif start is not None:
            if index - start >= minimum:
                runs.append((start, data[start:index].decode("latin1", errors="replace")))
            start = None

    return runs


def _tagged_text_fields(data: bytes, tag: int) -> list[tuple[int, str]]:
    fields: list[tuple[int, str]] = []
    marker = tag.to_bytes(2, "little")

    for marker_offset in range(2, len(data) - 4):
        if data[marker_offset : marker_offset + 2] != marker:
            continue
        encoded_length = int.from_bytes(data[marker_offset - 2 : marker_offset], "little")
        text_length = encoded_length - 4
        if not 1 <= text_length <= 80:
            continue
        start = marker_offset + 2
        end = start + text_length
        if end > len(data):
            continue
        raw = data[start:end]
        try:
            value = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if not re.fullmatch(r"[A-Za-z][A-Za-z .'\-]*", value):
            continue
        fields.append((start, value))

    return fields


def extract_people(data: bytes) -> list[PersonCandidate]:
    """Return person-name candidates from known given/surname field tags.

    Reunion can store the surname before or after the given name, so fields are
    decoded independently and paired only when they occur within the same small
    record neighbourhood.
    """
    given_fields = _tagged_text_fields(data, 0x001E)
    surname_fields = _tagged_text_fields(data, 0x0023)
    people: list[PersonCandidate] = []
    seen: set[tuple[int, str, str]] = set()

    for given_offset, given in given_fields:
        nearby = [
            (abs(surname_offset - given_offset), surname_offset, surname)
            for surname_offset, surname in surname_fields
            if abs(surname_offset - given_offset) <= 48
        ]
        if not nearby:
            continue
        _, surname_offset, surname = min(nearby)
        key = (min(given_offset, surname_offset), given, surname)
        if key in seen:
            continue
        seen.add(key)
        people.append(
            PersonCandidate(
                offset=min(given_offset, surname_offset),
                given=given,
                surname=surname,
                display=f"{given} {surname.title()}",
            )
        )

    return sorted(people, key=lambda item: item.offset)


def build_inventory(package_path: str | Path) -> PackageInventory:
    reader = BinaryReader(package_path)
    package = reader.inspect()
    data = reader.read_main_data()

    files: list[FileInventory] = []
    total_size = 0
    thumbnail_counts = ThumbnailInventory()

    for path in sorted(package.package_path.rglob("*")):
        if not path.is_file() or path.name.startswith("._"):
            continue
        relative = path.relative_to(package.package_path)
        size = path.stat().st_size
        total_size += size
        category = _category(path, package.main_data_path)
        files.append(
            FileInventory(
                name=path.name,
                relative_path=str(relative),
                size=size,
                category=category,
            )
        )

        if category == "thumbnail":
            thumbnail_counts.total += 1
            if re.match(r"p\d+-", path.name):
                thumbnail_counts.person += 1
            elif re.match(r"f\d+-", path.name):
                thumbnail_counts.family += 1
            else:
                thumbnail_counts.unknown += 1

    runs = _ascii_runs(data)
    person_tags = 0
    media_strings = 0
    path_strings = 0

    for _, text in runs:
        person_tags += len(re.findall(r"\[\[pt:\d+\]\]", text))
        if text.lower().endswith(_MEDIA_SUFFIXES):
            media_strings += 1
        if "Users/" in text or "/users/" in text.lower() or "Macintosh HD:" in text:
            path_strings += 1

    warnings = [
        "Person extraction is experimental and may include false positives until record boundaries are decoded.",
        "Index counts are labelled as slots until deleted and reserved record behaviour is decoded.",
    ]

    return PackageInventory(
        package_path=str(package.package_path),
        version=package.version,
        main_data_path=str(package.main_data_path),
        main_data_size=package.main_data_size,
        total_files=len(files),
        total_package_size=total_size,
        files=files,
        people=extract_people(data),
        person_tags=person_tags,
        media_strings=media_strings,
        path_strings=path_strings,
        thumbnails=thumbnail_counts,
        caches=build_cache_summary(package.package_path),
        warnings=warnings,
    )
