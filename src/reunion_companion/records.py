from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import re

from .dates import decode_packed_date
from .inventory import _tagged_text_fields
from .models import Event, Note
from .parser import BinaryReader

_RECORD_MAGIC = b"\x05\x03\x02\x01"
_BIRTH_EVENT_TAG = b"\xe8\x03"
_DATE_FIELD_MARKER = b"\x0a\x00\x08\x00\x00\x00"
_INLINE_DATE_MARKER = b"\x08\x00\x00\x00"
_PT_TAG = re.compile(rb"\[\[pt:(\d+)\]\]")


@dataclass(slots=True)
class StructuredPerson:
    record_id: int
    given: str
    surname: str
    display: str
    sex_code: int | None
    sex: str | None
    offset: int
    record_length: int
    parent_family_ids: list[int] = field(default_factory=list)
    raw_family_values: list[int] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)


@dataclass(slots=True)
class StructuredFamily:
    family_id: int
    spouse_ids: list[int] = field(default_factory=list)
    child_ids: list[int] = field(default_factory=list)
    spouse_link_status: str = "unknown"
    child_link_status: str = "decoded"
    events: list[Event] = field(default_factory=list)
    offset: int | None = None
    record_length: int | None = None


@dataclass(slots=True)
class TreeExtraction:
    package_path: str
    version: str
    people: list[StructuredPerson]
    families: list[StructuredFamily]
    warnings: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _field_u16(data: bytes, tag: int) -> list[int]:
    marker = tag.to_bytes(2, "little")
    values: list[int] = []
    for offset in range(1, len(data) - 4):
        if data[offset : offset + 2] != marker:
            continue
        if data[offset - 1] != 0:
            continue
        values.append(int.from_bytes(data[offset + 2 : offset + 4], "little"))
    return values


def _field_u32(data: bytes, tag: int) -> list[int]:
    marker = b"\x08\x00" + tag.to_bytes(2, "little")
    values: list[int] = []
    start = 0
    while True:
        offset = data.find(marker, start)
        if offset < 0:
            break
        value_start = offset + 4
        value_end = value_start + 4
        if value_end <= len(data):
            values.append(int.from_bytes(data[value_start:value_end], "little"))
        start = offset + 1
    return values


def _record_candidates(data: bytes) -> list[tuple[int, int, int, bytes]]:
    records: list[tuple[int, int, int, bytes]] = []
    start = 0
    while True:
        magic_offset = data.find(_RECORD_MAGIC, start)
        if magic_offset < 0:
            break
        if magic_offset < 2 or magic_offset + 12 > len(data):
            start = magic_offset + 1
            continue

        record_start = magic_offset - 2
        payload_length = int.from_bytes(data[magic_offset + 4 : magic_offset + 8], "little")
        record_id = int.from_bytes(data[magic_offset + 8 : magic_offset + 12], "little")

        if 16 <= payload_length <= 64_000:
            record_end = magic_offset + 8 + payload_length
            if record_end <= len(data):
                records.append(
                    (record_start, payload_length, record_id, data[record_start:record_end])
                )
        start = magic_offset + 1
    return records


def _decode_name(record: bytes) -> tuple[str, str] | None:
    given_fields = _tagged_text_fields(record, 0x001E)
    surname_fields = _tagged_text_fields(record, 0x0023)
    if not given_fields or not surname_fields:
        return None

    best: tuple[int, str, str] | None = None
    for given_offset, given in given_fields:
        for surname_offset, surname in surname_fields:
            distance = abs(given_offset - surname_offset)
            if distance <= 64 and (best is None or distance < best[0]):
                best = (distance, given, surname)
    if best is None:
        return None
    return best[1], best[2]



def _decode_place_token(record: bytes, date_end: int) -> tuple[int | None, int]:
    """Decode the ``[[pt:n]]`` place token following an event date.

    Controlled probes show three null separator bytes between the four-byte
    packed date and the token. The decoder permits zero to four null bytes so
    it remains conservative across otherwise equivalent event envelopes.
    """
    token_start = date_end
    null_count = 0
    while (
        token_start < len(record)
        and record[token_start] == 0
        and null_count < 4
    ):
        token_start += 1
        null_count += 1

    match = _PT_TAG.match(record, token_start)
    if match is None or match.start() != token_start:
        return None, date_end
    return int(match.group(1)), match.end()


def _decode_memo_after_date(record: bytes, content_start: int) -> str | None:
    """Decode the optional length-prefixed event memo.

    When a place token is present, ``content_start`` points immediately after
    it. For older probe shapes, the function also retains a fallback search for
    a place token before the memo.
    """
    length_start = content_start

    if length_start + 4 <= len(record):
        length = int.from_bytes(record[length_start : length_start + 4], "little")
        text_length = length - 4
        if 1 <= text_length <= 100_000:
            text_start = length_start + 4
            text_end = text_start + text_length
            if text_end <= len(record):
                try:
                    text = record[text_start:text_end].decode("utf-8")
                except UnicodeDecodeError:
                    pass
                else:
                    if text.isprintable():
                        return text

    match = _PT_TAG.search(record, content_start)
    if match is None:
        return None
    length_start = match.end()
    if length_start + 4 > len(record):
        return None
    length = int.from_bytes(record[length_start : length_start + 4], "little")
    text_length = length - 4
    if not 1 <= text_length <= 100_000:
        return None
    text_start = length_start + 4
    text_end = text_start + text_length
    if text_end > len(record):
        return None
    try:
        text = record[text_start:text_end].decode("utf-8")
    except UnicodeDecodeError:
        return None
    return text if text.isprintable() else None


def _decode_birth_event(record: bytes, record_offset: int) -> Event | None:
    event_start = record.find(_BIRTH_EVENT_TAG)
    if event_start < 0:
        return None

    date_marker = record.find(_DATE_FIELD_MARKER, event_start)
    if date_marker < 0 or date_marker + 11 > len(record):
        return None

    qualifier = record[date_marker + 6]
    raw_date = record[date_marker + 7 : date_marker + 11]
    try:
        date = decode_packed_date(raw_date, qualifier=qualifier)
    except ValueError:
        return None

    date_end = date_marker + 11
    place_id, content_start = _decode_place_token(record, date_end)
    memo = _decode_memo_after_date(record, content_start)
    return Event(
        event_type="birth",
        date=date,
        place_id=place_id,
        memo=memo,
        raw_offset=record_offset + date_marker,
        decode_status="decoded-controlled-probes",
    )


def _plausible_inline_dates(record: bytes, start: int = 0) -> list[tuple[int, object]]:
    results: list[tuple[int, object]] = []
    cursor = start
    while True:
        marker = record.find(_INLINE_DATE_MARKER, cursor)
        if marker < 0:
            break
        if marker + 9 <= len(record):
            qualifier = record[marker + 4]
            raw_date = record[marker + 5 : marker + 9]
            try:
                date = decode_packed_date(raw_date, qualifier=qualifier)
            except ValueError:
                pass
            else:
                if 1000 <= date.year <= 2200:
                    results.append((marker, date))
        cursor = marker + 1
    return results


def _decode_family_record(
    record_id: int,
    record: bytes,
    offset: int,
    payload_length: int,
) -> StructuredFamily | None:
    spouse_a = _field_u32(record, 0x0050)
    spouse_b = _field_u32(record, 0x0051)
    if not spouse_a or not spouse_b:
        return None

    events: list[Event] = []
    date_candidates = _plausible_inline_dates(record)
    if date_candidates:
        date_offset, date = date_candidates[-1]
        date_end = date_offset + 9
        place_id, _content_start = _decode_place_token(record, date_end)
        events.append(
            Event(
                event_type="marriage",
                date=date,
                place_id=place_id,
                raw_offset=offset + date_offset,
                decode_status="decoded-controlled-probes",
            )
        )

    return StructuredFamily(
        family_id=record_id,
        spouse_ids=[spouse_a[0], spouse_b[0]],
        spouse_link_status="decoded",
        events=events,
        offset=offset,
        record_length=payload_length,
    )



def extract_person_notes(data: bytes) -> dict[int, list[Note]]:
    """Decode standalone Reunion 14 person-note records.

    Probe-17 establishes that a general person note is stored in a separate
    record envelope whose record ID is the owning person ID. The payload uses
    the marker ``talfa`` followed by null padding and plain UTF-8 text.
    """
    notes: dict[int, list[Note]] = {}
    cursor = 0
    while True:
        marker = data.find(b"talfa", cursor)
        if marker < 0:
            break
        magic = data.rfind(_RECORD_MAGIC, max(0, marker - 64), marker)
        if magic < 0 or magic + 12 > len(data):
            cursor = marker + 5
            continue
        owner_id = int.from_bytes(data[magic + 8 : magic + 12], "little")
        if owner_id <= 0:
            cursor = marker + 5
            continue
        text_start = marker + len(b"talfa")
        while text_start < len(data) and data[text_start] == 0:
            text_start += 1
        text_end = data.find(b"\x00", text_start)
        if text_end < 0:
            text_end = len(data)
        raw = data[text_start:text_end]
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            cursor = marker + 5
            continue
        if text.strip():
            notes.setdefault(owner_id, []).append(
                Note(
                    note_type="person",
                    text=text,
                    format="plain",
                    raw_offset=text_start,
                )
            )
        cursor = marker + 5
    return notes


def extract_structured_people(data: bytes) -> list[StructuredPerson]:
    people: list[StructuredPerson] = []
    seen_ids: set[int] = set()

    for offset, payload_length, record_id, record in _record_candidates(data):
        name = _decode_name(record)
        if name is None or record_id <= 0 or record_id in seen_ids:
            continue

        given, surname = name
        sex_values = _field_u16(record, 0x001B)
        sex_code = sex_values[0] if sex_values else None
        sex = {1: "male", 2: "female"}.get(sex_code)
        parent_family_ids = [value for value in _field_u32(record, 0x003C) if value > 0]
        raw_family_values = [value for value in _field_u32(record, 0x0064) if value > 0]

        events: list[Event] = []
        birth_event = _decode_birth_event(record, offset)
        if birth_event is not None:
            events.append(birth_event)

        people.append(
            StructuredPerson(
                record_id=record_id,
                given=given,
                surname=surname,
                display=f"{given} {surname.title()}",
                sex_code=sex_code,
                sex=sex,
                offset=offset,
                record_length=payload_length,
                parent_family_ids=parent_family_ids,
                raw_family_values=raw_family_values,
                events=events,
            )
        )
        seen_ids.add(record_id)

    return sorted(people, key=lambda person: person.record_id)


def extract_structured_families(data: bytes) -> list[StructuredFamily]:
    families: list[StructuredFamily] = []
    seen_ids: set[int] = set()
    for offset, payload_length, record_id, record in _record_candidates(data):
        family = _decode_family_record(record_id, record, offset, payload_length)
        if family is None or family.family_id in seen_ids:
            continue
        families.append(family)
        seen_ids.add(family.family_id)
    return sorted(families, key=lambda family: family.family_id)


def build_families(
    people: list[StructuredPerson],
    decoded_families: list[StructuredFamily],
    family_slots: int,
) -> list[StructuredFamily]:
    by_id = {family.family_id: family for family in decoded_families}
    for family_id in range(1, family_slots + 1):
        by_id.setdefault(family_id, StructuredFamily(family_id=family_id))

    for person in people:
        for family_id in person.parent_family_ids:
            family = by_id.get(family_id)
            if family is not None and person.record_id not in family.child_ids:
                family.child_ids.append(person.record_id)

    return [by_id[key] for key in sorted(by_id)]


def extract_tree(package_path: str | Path) -> TreeExtraction:
    reader = BinaryReader(package_path)
    package = reader.inspect()
    data = reader.read_main_data()

    from .caches import build_cache_summary, decode_place_map

    caches = build_cache_summary(package.package_path)
    family_slots = caches.index.family_slots if caches.index else 0
    people = extract_structured_people(data)
    person_notes = extract_person_notes(data)
    for person in people:
        person.notes.extend(person_notes.get(person.record_id, []))
    decoded_families = extract_structured_families(data)
    families = build_families(people, decoded_families, family_slots)

    place_map: dict[int, str] = {}
    places_path = package.package_path / "places.cache"
    if places_path.is_file():
        try:
            place_map = decode_place_map(places_path.read_bytes())
        except Exception:
            place_map = {}

    for person in people:
        for event in person.events:
            if event.place_id is not None:
                event.place = place_map.get(event.place_id)
    for family in families:
        for event in family.events:
            if event.place_id is not None:
                event.place = place_map.get(event.place_id)

    warnings = [
        "Person IDs, sex codes, birth dates, and direct spouse IDs are decoded from controlled Reunion 14 records.",
        "Child-to-family links use the observed 0x003C field and remain experimental until confirmed by additional family shapes.",
        "Marriage dates are decoded from the controlled family-event record pattern.",
        "Event place IDs are decoded from length-prefixed [[pt:n]] tokens and resolved through places.cache.",
        "General person notes are decoded from standalone talfa records.",
        "Raw 0x0064 values are preserved but not assigned a meaning.",
        "Read-only: no Reunion package files were changed.",
    ]

    return TreeExtraction(
        package_path=str(package.package_path),
        version=package.version,
        people=people,
        families=families,
        warnings=warnings,
    )
