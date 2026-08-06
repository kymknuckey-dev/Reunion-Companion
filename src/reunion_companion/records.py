from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import re

from .inventory import _tagged_text_fields
from .parser import BinaryReader

_RECORD_MAGIC = b"\x05\x03\x02\x01"


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


@dataclass(slots=True)
class StructuredFamily:
    family_id: int
    spouse_ids: list[int] = field(default_factory=list)
    child_ids: list[int] = field(default_factory=list)
    spouse_link_status: str = "unknown"
    child_link_status: str = "decoded"


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
    """Read compact 2-byte values from the observed five-byte scalar field."""
    marker = tag.to_bytes(2, "little")
    values: list[int] = []
    for offset in range(1, len(data) - 4):
        if data[offset : offset + 2] != marker:
            continue
        # Observed scalar form: 00 | tag:u16 | value:u16
        if data[offset - 1] != 0:
            continue
        values.append(int.from_bytes(data[offset + 2 : offset + 4], "little"))
    return values


def _field_u32(data: bytes, tag: int) -> list[int]:
    """Read fixed eight-byte fields: encoded length 8, tag, then uint32."""
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
    """Return observed Reunion record envelopes.

    The controlled Reunion 14 probes show:
      prefix:u16 | magic | payload_length:u32 | record_id:u32 | ...

    We retain only envelopes whose declared payload fits inside the file.
    """
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

        # Probe person records are small. A generous ceiling avoids accepting
        # unrelated large blocks while leaving room for notes and events.
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

        # Tag 0x003C is directly observed on Baby Probe after adding the child
        # to Family 1. Until more probes exist, keep the tag name conservative.
        parent_family_ids = [value for value in _field_u32(record, 0x003C) if value > 0]

        # Tag 0x0064 is retained raw only. Its semantics are not yet proven.
        raw_family_values = [value for value in _field_u32(record, 0x0064) if value > 0]

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
            )
        )
        seen_ids.add(record_id)

    return sorted(people, key=lambda person: person.record_id)


def build_families(
    people: list[StructuredPerson],
    family_slots: int,
) -> list[StructuredFamily]:
    families = [StructuredFamily(family_id=index) for index in range(1, family_slots + 1)]

    for person in people:
        for family_id in person.parent_family_ids:
            if 1 <= family_id <= len(families):
                families[family_id - 1].child_ids.append(person.record_id)

    # Provisional spouse inference for the controlled simple-family pattern:
    # a family has decoded children, exactly two people are not children of any
    # family, and there is only one family slot. This is never represented as a
    # decoded pointer.
    if len(families) == 1:
        child_ids = set(families[0].child_ids)
        possible_spouses = [
            person.record_id
            for person in people
            if person.record_id not in child_ids and not person.parent_family_ids
        ]
        if len(possible_spouses) == 2:
            families[0].spouse_ids = possible_spouses
            families[0].spouse_link_status = "inferred-controlled-pattern"

    return families


def extract_tree(package_path: str | Path) -> TreeExtraction:
    reader = BinaryReader(package_path)
    package = reader.inspect()
    data = reader.read_main_data()

    from .caches import build_cache_summary

    caches = build_cache_summary(package.package_path)
    family_slots = caches.index.family_slots if caches.index else 0
    people = extract_structured_people(data)
    families = build_families(people, family_slots)

    warnings = [
        "Person IDs and sex codes are decoded from controlled Reunion 14 record envelopes.",
        "Child-to-family links use the observed 0x003C field and remain experimental until confirmed by more family shapes.",
        "Spouse links are inferred only for the one-family/two-parent controlled pattern; no spouse pointer has yet been decoded.",
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
