from __future__ import annotations

from pathlib import Path

from .inventory import _tagged_text_fields
from .models import Source
from .parser import BinaryReader

_RECORD_MAGIC = b"\x05\x03\x02\x01"


def _record_envelopes(data: bytes):
    start = 0
    while True:
        magic = data.find(_RECORD_MAGIC, start)
        if magic < 0:
            return
        if magic >= 2 and magic + 12 <= len(data):
            record_start = magic - 2
            payload_length = int.from_bytes(data[magic + 4 : magic + 8], "little")
            record_id = int.from_bytes(data[magic + 8 : magic + 12], "little")
            next_magic = data.find(_RECORD_MAGIC, magic + 1)
            record_end = next_magic - 2 if next_magic >= 2 else len(data)
            if 16 <= payload_length <= 4096 and record_end > record_start:
                yield record_start, payload_length, record_id, data[record_start:record_end]
        start = magic + 1


def extract_sources_from_data(data: bytes) -> list[Source]:
    """Decode controlled Reunion free-form master source records.

    Probe-21 establishes field tag 0x0014 as the source title inside a compact
    record envelope whose record ID is the Source ID.
    """
    sources: list[Source] = []
    seen: set[int] = set()

    for offset, _length, record_id, record in _record_envelopes(data):
        if record_id <= 0 or record_id in seen:
            continue
        # Built-in event/source-template definition records carry the
        # fixed marker `52tj`; user-created master source records do not.
        if b"52tj" in record[:32]:
            continue
        title_fields = _tagged_text_fields(record, 0x0014)
        if not title_fields:
            continue

        # Free-form source title records in Probe-21 contain one concise title.
        candidates = [
            value.strip()
            for _field_offset, value in title_fields
            if value.strip() and len(value.strip()) <= 500
        ]
        if not candidates:
            continue

        title = candidates[0]
        sources.append(
            Source(
                source_id=record_id,
                title=title,
                raw_offset=offset,
            )
        )
        seen.add(record_id)

    return sorted(sources, key=lambda source: source.source_id)


def extract_sources(package_path: str | Path) -> list[Source]:
    reader = BinaryReader(package_path)
    return extract_sources_from_data(reader.read_main_data())
