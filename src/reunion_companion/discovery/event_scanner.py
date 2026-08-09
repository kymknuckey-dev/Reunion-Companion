"""Raw event archaeology for Reunion 14 family data.

This module intentionally does not assign unknown event types. It observes
date-bearing structures inside named person records, records their surrounding
binary signature, and groups recurring layouts for later human/probe review.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from reunion_companion.dates import decode_packed_date
from reunion_companion.parser import BinaryReader
from reunion_companion.records import _decode_name, _record_candidates

_DATE_FIELD_MARKER = b"\x0a\x00\x08\x00\x00\x00"
_PT_PREFIX = b"[[pt:"


@dataclass(frozen=True, slots=True)
class EventObservation:
    person_id: int
    person_name: str
    record_offset: int
    record_length: int
    marker_offset: int
    raw_date_offset: int
    date_display: str
    qualifier: int
    place_token: str | None
    memo_candidate: bool
    signature: str
    context_hex: str
    capture_start: int = 0
    capture_end: int = 0
    capture_hex: str = ""
    capture_truncated_left: bool = False
    capture_truncated_right: bool = False

    @property
    def absolute_offset(self) -> int:
        return self.record_offset + self.marker_offset

    @property
    def capture_length(self) -> int:
        return max(0, self.capture_end - self.capture_start)

    @property
    def marker_offset_in_capture(self) -> int:
        return self.marker_offset - self.capture_start


@dataclass(frozen=True, slots=True)
class EventSignature:
    signature: str
    count: int
    sample_person_ids: tuple[int, ...]
    sample_dates: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EventScan:
    package_path: str
    main_data_size: int
    named_person_records: int
    observations: tuple[EventObservation, ...]
    signatures: tuple[EventSignature, ...]

    @property
    def observation_count(self) -> int:
        return len(self.observations)

    @property
    def signature_count(self) -> int:
        return len(self.signatures)

    def for_person(self, person_id: int) -> list[EventObservation]:
        return [item for item in self.observations if item.person_id == person_id]


def _place_token(record: bytes, start: int) -> str | None:
    cursor = start
    nulls = 0
    while cursor < len(record) and record[cursor] == 0 and nulls < 4:
        cursor += 1
        nulls += 1

    if not record.startswith(_PT_PREFIX, cursor):
        return None

    end = record.find(b"]]", cursor)
    if end < 0 or end - cursor > 24:
        return None

    raw = record[cursor : end + 2]
    try:
        return raw.decode("ascii")
    except UnicodeDecodeError:
        return None


def _memo_candidate(record: bytes, start: int) -> bool:
    cursor = start
    nulls = 0
    while cursor < len(record) and record[cursor] == 0 and nulls < 4:
        cursor += 1
        nulls += 1

    if record.startswith(_PT_PREFIX, cursor):
        end = record.find(b"]]", cursor)
        if end >= 0:
            cursor = end + 2

    if cursor + 4 > len(record):
        return False

    encoded_length = int.from_bytes(record[cursor : cursor + 4], "little")
    text_length = encoded_length - 4
    if not 1 <= text_length <= 100_000:
        return False

    text_start = cursor + 4
    text_end = text_start + text_length
    if text_end > len(record):
        return False

    try:
        text = record[text_start:text_end].decode("utf-8")
    except UnicodeDecodeError:
        return False
    return bool(text.strip()) and text.isprintable()


def _signature(record: bytes, marker_offset: int) -> tuple[str, str]:
    """Return stable pre-marker signature and a wider context hex string.

    The signature is the 12 bytes immediately before the generic date marker.
    We do not interpret these bytes; recurring values are useful for clustering.
    """
    sig_start = max(0, marker_offset - 12)
    signature_bytes = record[sig_start:marker_offset]

    context_start = max(0, marker_offset - 24)
    context_end = min(len(record), marker_offset + 24)
    context = record[context_start:context_end]

    return signature_bytes.hex(" "), context.hex(" ")


def scan_event_observations(
    data: bytes,
    *,
    capture_pre_bytes: int = 64,
    capture_post_bytes: int = 512,
) -> tuple[list[EventObservation], int]:
    observations: list[EventObservation] = []
    named_records = 0

    for record_offset, payload_length, record_id, record in _record_candidates(data):
        if record_id <= 0:
            continue
        name = _decode_name(record)
        if name is None:
            continue

        named_records += 1
        person_name = f"{name[0]} {name[1].title()}"

        cursor = 0
        while True:
            marker = record.find(_DATE_FIELD_MARKER, cursor)
            if marker < 0:
                break

            # generic marker + qualifier + four-byte packed date
            if marker + 11 <= len(record):
                qualifier = record[marker + 6]
                raw_date = record[marker + 7 : marker + 11]
                try:
                    date = decode_packed_date(raw_date, qualifier=qualifier)
                except ValueError:
                    pass
                else:
                    if 1000 <= date.year <= 2200:
                        date_end = marker + 11
                        token = _place_token(record, date_end)
                        sig, context = _signature(record, marker)
                        capture_start = max(0, marker - capture_pre_bytes)
                        capture_end = min(len(record), marker + capture_post_bytes)
                        capture = record[capture_start:capture_end]

                        observations.append(
                            EventObservation(
                                person_id=record_id,
                                person_name=person_name,
                                record_offset=record_offset,
                                record_length=payload_length,
                                marker_offset=marker,
                                raw_date_offset=marker + 7,
                                date_display=date.display,
                                qualifier=qualifier,
                                place_token=token,
                                memo_candidate=_memo_candidate(record, date_end),
                                signature=sig,
                                context_hex=context,
                                capture_start=capture_start,
                                capture_end=capture_end,
                                capture_hex=capture.hex(" "),
                                capture_truncated_left=capture_start > 0,
                                capture_truncated_right=capture_end < len(record),
                            )
                        )
            cursor = marker + 1

    return observations, named_records


def cluster_event_signatures(
    observations: list[EventObservation],
) -> list[EventSignature]:
    counts = Counter(item.signature for item in observations)
    grouped: dict[str, list[EventObservation]] = {}
    for item in observations:
        grouped.setdefault(item.signature, []).append(item)

    clusters: list[EventSignature] = []
    for signature, count in counts.most_common():
        samples = grouped[signature]
        clusters.append(
            EventSignature(
                signature=signature,
                count=count,
                sample_person_ids=tuple(item.person_id for item in samples[:5]),
                sample_dates=tuple(item.date_display for item in samples[:5]),
            )
        )
    return clusters


class EventScanner:
    """Scan the main Reunion family data for person event candidates."""

    def __init__(
        self,
        *,
        capture_pre_bytes: int = 64,
        capture_post_bytes: int = 512,
    ) -> None:
        self.capture_pre_bytes = capture_pre_bytes
        self.capture_post_bytes = capture_post_bytes

    def scan(self, package_path: str | Path) -> EventScan:
        reader = BinaryReader(package_path)
        package = reader.inspect()
        data = reader.read_main_data()

        observations, named_records = scan_event_observations(
            data,
            capture_pre_bytes=self.capture_pre_bytes,
            capture_post_bytes=self.capture_post_bytes,
        )
        signatures = cluster_event_signatures(observations)

        return EventScan(
            package_path=str(package.package_path),
            main_data_size=len(data),
            named_person_records=named_records,
            observations=tuple(observations),
            signatures=tuple(signatures),
        )
