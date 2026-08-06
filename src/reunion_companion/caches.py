from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import re


class CacheDecodeError(ValueError):
    """Raised when a cache does not match the currently supported structure."""


@dataclass(slots=True)
class NamedCache:
    filename: str
    signature: str
    declared_size: int
    declared_count: int | None
    values: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class IndexCache:
    filename: str
    signature: str
    declared_size: int
    primary_slots: int
    family_slots: int
    trailing_ids: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class CacheSummary:
    given_names: NamedCache | None = None
    surnames: NamedCache | None = None
    places: NamedCache | None = None
    index: IndexCache | None = None
    place_usage_count: int | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _u32(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise CacheDecodeError(f"Cannot read uint32 at offset {offset}")
    return int.from_bytes(data[offset : offset + 4], "little", signed=False)


def _header(data: bytes, expected_signature: bytes) -> tuple[int, str]:
    if len(data) < 8:
        raise CacheDecodeError("Cache is shorter than its eight-byte header")
    declared_size = _u32(data, 0)
    signature_bytes = data[4:8]
    if signature_bytes != expected_signature:
        raise CacheDecodeError(
            f"Expected signature {expected_signature!r}, found {signature_bytes!r}"
        )
    if declared_size != len(data):
        raise CacheDecodeError(
            f"Declared cache size {declared_size} does not match actual size {len(data)}"
        )
    return declared_size, signature_bytes.decode("ascii")


def _clean_text(raw: bytes) -> str:
    value = raw.rstrip(b"\x00").decode("utf-8", errors="strict").strip()
    if not value:
        raise CacheDecodeError("Decoded an empty text value")
    return value


def decode_fmnames(data: bytes) -> NamedCache:
    """Decode Reunion 14's first/middle-name search cache.

    Controlled probes establish a count at offset 8, an offset table beginning
    at offset 12, and entry text beginning eight bytes into each entry.
    """
    declared_size, signature = _header(data, b"2wps")
    count = _u32(data, 8)
    table_end = 12 + (count * 4)
    if table_end > len(data):
        raise CacheDecodeError("Given-name offset table extends beyond cache")

    offsets = [_u32(data, 12 + (index * 4)) for index in range(count)]
    values: list[str] = []
    for index, offset in enumerate(offsets):
        end = offsets[index + 1] if index + 1 < count else len(data)
        if offset < table_end or offset + 8 > end or end > len(data):
            raise CacheDecodeError(f"Invalid given-name entry boundaries at offset {offset}")
        values.append(_clean_text(data[offset + 8 : end]))

    return NamedCache("fmnames.cache", signature, declared_size, count, values)



@dataclass(slots=True)
class PlaceRecord:
    record_id: int
    value: str


def decode_place_records(data: bytes) -> list[PlaceRecord]:
    """Decode Reunion 14 place IDs and names.

    Controlled probes establish a place entry layout containing:
      entry_size:u32
      usage_or_sort_value:u32
      hash:u32
      place_id:u32
      UTF-8 place text
    """
    _declared_size, _signature = _header(data, b"ahcp")
    count = _u32(data, 8)
    table_start = 16
    table_end = table_start + (count * 4)
    if table_end > len(data):
        raise CacheDecodeError("Place offset table extends beyond cache")

    offsets = [_u32(data, table_start + (index * 4)) for index in range(count)]
    records: list[PlaceRecord] = []
    for index, offset in enumerate(offsets):
        end = offsets[index + 1] if index + 1 < count else len(data)
        if offset < table_end or offset + 16 > end or end > len(data):
            raise CacheDecodeError(f"Invalid place entry boundaries at offset {offset}")
        entry_size = _u32(data, offset)
        if offset + entry_size != end:
            raise CacheDecodeError(
                f"Place entry at {offset} declares {entry_size} bytes but occupies {end - offset}"
            )
        place_id = _u32(data, offset + 12)
        value = _clean_text(data[offset + 16 : end])
        records.append(PlaceRecord(record_id=place_id, value=value))
    return records


def decode_place_map(data: bytes) -> dict[int, str]:
    return {record.record_id: record.value for record in decode_place_records(data)}


def decode_places(data: bytes) -> NamedCache:
    """Decode Reunion 14's unique-place catalogue."""
    declared_size, signature = _header(data, b"ahcp")
    records = decode_place_records(data)
    return NamedCache(
        "places.cache",
        signature,
        declared_size,
        len(records),
        [record.value for record in records],
    )


def decode_surnames(data: bytes) -> NamedCache:
    """Decode readable surnames from Reunion 14's compact surname cache.

    The cache does not expose the same offset table as fmnames.cache. Controlled
    files show a fixed eight-byte header followed by compact binary metadata and
    uppercase UTF-8 surname strings. Until the entry metadata is fully mapped,
    this decoder extracts only conservative alphabetic runs.
    """
    declared_size, signature = _header(data, b"10ns")
    body = data[8:]
    values: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(rb"[A-Za-z][A-Za-z' -]{2,}", body):
        value = match.group(0).decode("ascii").strip()
        if value and value not in seen:
            seen.add(value)
            values.append(value.title())

    declared_count = int.from_bytes(data[10:12], "little")
    return NamedCache("surnames.cache", signature, declared_size, declared_count, values)


def decode_index(data: bytes) -> IndexCache:
    """Decode the proven header and trailing 32-bit IDs from index.cache.

    `primary_slots` and `family_slots` are deliberately neutral names. Probe
    files track them with person and family additions, but deleted or reserved
    records may make them differ from visible record totals in real databases.
    """
    declared_size, signature = _header(data, b"09ci")
    if len(data) < 16:
        raise CacheDecodeError("Index cache is too short")
    primary_slots = _u32(data, 8)
    family_slots = _u32(data, 12)

    # Controlled probes show a fixed 48-byte prefix followed by four-byte IDs.
    trailing_ids: list[int] = []
    if len(data) >= 48 and (len(data) - 48) % 4 == 0:
        trailing_ids = [_u32(data, offset) for offset in range(48, len(data), 4)]

    return IndexCache(
        filename="index.cache",
        signature=signature,
        declared_size=declared_size,
        primary_slots=primary_slots,
        family_slots=family_slots,
        trailing_ids=trailing_ids,
    )


def decode_place_usage_count(data: bytes) -> int:
    _header(data, b"hcup")
    return _u32(data, 8)


def _tagged_surnames_from_main_data(data: bytes) -> list[str]:
    """Extract surname field values using the proven 0x0023 text tag."""
    marker = (0x0023).to_bytes(2, "little")
    values: list[str] = []
    seen: set[str] = set()
    for marker_offset in range(2, len(data) - 4):
        if data[marker_offset : marker_offset + 2] != marker:
            continue
        encoded_length = int.from_bytes(data[marker_offset - 2 : marker_offset], "little")
        text_length = encoded_length - 4
        if not 1 <= text_length <= 100:
            continue
        start = marker_offset + 2
        end = start + text_length
        if end > len(data):
            continue
        try:
            value = data[start:end].decode("utf-8").strip()
        except UnicodeDecodeError:
            continue
        if not re.fullmatch(r"[A-Za-z][A-Za-z .'\-]*", value):
            continue
        normalised = value.title()
        if normalised not in seen:
            seen.add(normalised)
            values.append(normalised)
    return sorted(values)


def build_cache_summary(package_path: str | Path) -> CacheSummary:
    package = Path(package_path)
    summary = CacheSummary()

    decoders = [
        ("fmnames.cache", "given_names", decode_fmnames),
        ("surnames.cache", "surnames", decode_surnames),
        ("places.cache", "places", decode_places),
        ("index.cache", "index", decode_index),
    ]

    for filename, attribute, decoder in decoders:
        path = package / filename
        if not path.is_file():
            summary.warnings.append(f"{filename} is not present")
            continue
        try:
            setattr(summary, attribute, decoder(path.read_bytes()))
        except (CacheDecodeError, UnicodeDecodeError) as exc:
            summary.warnings.append(f"Could not decode {filename}: {exc}")

    # The compact surname-cache entry metadata is not fully decoded. When the
    # main data file is available, use its proven surname text fields to avoid
    # mistaking binary metadata bytes for surname characters.
    main_path = package / "familyfile.familydata"
    if summary.surnames is not None and main_path.is_file():
        main_surnames = _tagged_surnames_from_main_data(main_path.read_bytes())
        if main_surnames:
            summary.surnames.values = main_surnames

    usage_path = package / "placeUsage.cache"
    if usage_path.is_file():
        try:
            summary.place_usage_count = decode_place_usage_count(usage_path.read_bytes())
        except CacheDecodeError as exc:
            summary.warnings.append(f"Could not decode placeUsage.cache: {exc}")

    return summary
