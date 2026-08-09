"""Build 14 Differential Semantic Verification Engine.

This module deliberately begins with raw familyfile.familydata differences and
then overlays decoded/structural evidence from the existing Discovery stack.
It fixes Build 13's blind spot where an in-place value change could leave
object counts and graph topology unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from hashlib import sha256
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True, slots=True)
class ByteSpanDelta:
    tag: str
    before_start: int
    before_end: int
    after_start: int
    after_end: int
    before_hex: str
    after_hex: str
    before_ascii: str
    after_ascii: str

    @property
    def before_length(self) -> int:
        return self.before_end - self.before_start

    @property
    def after_length(self) -> int:
        return self.after_end - self.after_start


@dataclass(frozen=True, slots=True)
class DecodedEventDelta:
    person_id: int
    person_name: str
    before_date: str | None
    after_date: str | None
    before_place: str | None
    after_place: str | None
    before_qualifier: int | None
    after_qualifier: int | None
    before_record_offset: int | None
    after_record_offset: int | None
    likely_change: str


@dataclass(frozen=True, slots=True)
class DifferentialResult:
    declared_change: str
    before_path: str
    after_path: str
    before_hash: str
    after_hash: str
    before_size: int
    after_size: int
    byte_spans: tuple[ByteSpanDelta, ...]
    changed_before_bytes: int
    changed_after_bytes: int
    decoded_event_deltas: tuple[DecodedEventDelta, ...]
    class_deltas: tuple[tuple[str, int, int, int], ...]
    edge_deltas: tuple[tuple[str, str, int, int, int], ...]

    @property
    def raw_changed(self) -> bool:
        return self.before_hash != self.after_hash

    @property
    def structure_changed(self) -> bool:
        return bool(self.class_deltas or self.edge_deltas)


@dataclass(frozen=True, slots=True)
class PersonDifferential:
    person_id: int
    person_name: str
    event_deltas: tuple[DecodedEventDelta, ...]
    nearby_byte_spans: tuple[ByteSpanDelta, ...]


def _main_data_path(package_path: str | Path) -> Path:
    path = Path(package_path).expanduser()
    if path.is_dir():
        candidate = path / "familyfile.familydata"
        if candidate.is_file():
            return candidate
    if path.is_file():
        return path
    raise FileNotFoundError(f"Reunion main data not found: {path}")


def _digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def _ascii_preview(data: bytes, limit: int = 80) -> str:
    text = "".join(chr(b) if 32 <= b <= 126 else "." for b in data[:limit])
    return text + ("…" if len(data) > limit else "")


def _hex_preview(data: bytes, limit: int = 64) -> str:
    shown = data[:limit].hex(" ")
    return shown + (" …" if len(data) > limit else "")


def byte_differences(before: bytes, after: bytes) -> list[ByteSpanDelta]:
    """Return changed spans without turning offsets shifts into a false tail diff.

    Equal-length controlled edits are handled positionally and are extremely
    fast. For length-changing edits we first trim the common prefix/suffix and
    only align the changed middle. Very large rewritten middles are represented
    conservatively as one replacement span rather than performing an expensive
    quadratic alignment over the whole Reunion database.
    """
    def make(tag: str, i1: int, i2: int, j1: int, j2: int) -> ByteSpanDelta:
        left = before[i1:i2]
        right = after[j1:j2]
        return ByteSpanDelta(
            tag=tag,
            before_start=i1,
            before_end=i2,
            after_start=j1,
            after_end=j2,
            before_hex=_hex_preview(left),
            after_hex=_hex_preview(right),
            before_ascii=_ascii_preview(left),
            after_ascii=_ascii_preview(right),
        )

    if before == after:
        return []

    if len(before) == len(after):
        spans: list[ByteSpanDelta] = []
        index = 0
        while index < len(before):
            if before[index] == after[index]:
                index += 1
                continue
            start = index
            while index < len(before) and before[index] != after[index]:
                index += 1
            spans.append(make("replace", start, index, start, index))
        return spans

    prefix = 0
    limit = min(len(before), len(after))
    while prefix < limit and before[prefix] == after[prefix]:
        prefix += 1

    suffix = 0
    while (
        suffix < (len(before) - prefix)
        and suffix < (len(after) - prefix)
        and before[len(before) - 1 - suffix] == after[len(after) - 1 - suffix]
    ):
        suffix += 1

    b_end = len(before) - suffix
    a_end = len(after) - suffix
    b_mid = before[prefix:b_end]
    a_mid = after[prefix:a_end]

    if not b_mid:
        return [make("insert", prefix, prefix, prefix, a_end)]
    if not a_mid:
        return [make("delete", prefix, b_end, prefix, prefix)]

    if len(b_mid) <= 8192 and len(a_mid) <= 8192:
        matcher = SequenceMatcher(None, b_mid, a_mid, autojunk=True)
        spans: list[ByteSpanDelta] = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            spans.append(
                make(tag, prefix + i1, prefix + i2, prefix + j1, prefix + j2)
            )
        return spans

    return [make("replace", prefix, b_end, prefix, a_end)]


def _load_events(package_path: str | Path):
    try:
        from .event_scanner import EventScanner
    except Exception:
        return []
    try:
        scan = EventScanner().scan(Path(package_path).expanduser())
        return list(scan.observations)
    except Exception:
        return []


def _event_key(item, ordinal: int) -> tuple[int, int]:
    return (int(getattr(item, "person_id", -1)), ordinal)


def _group_events(events: Sequence) -> dict[int, list]:
    grouped: dict[int, list] = {}
    for event in events:
        grouped.setdefault(int(getattr(event, "person_id", -1)), []).append(event)
    for values in grouped.values():
        values.sort(key=lambda item: (
            int(getattr(item, "marker_offset", 0)),
            int(getattr(item, "raw_date_offset", 0)),
        ))
    return grouped


def decoded_event_differences(before_path: str | Path, after_path: str | Path) -> list[DecodedEventDelta]:
    before_events = _group_events(_load_events(before_path))
    after_events = _group_events(_load_events(after_path))
    deltas: list[DecodedEventDelta] = []

    for person_id in sorted(set(before_events) | set(after_events)):
        left = before_events.get(person_id, [])
        right = after_events.get(person_id, [])
        count = max(len(left), len(right))
        for index in range(count):
            b = left[index] if index < len(left) else None
            a = right[index] if index < len(right) else None
            bdate = getattr(b, "date_display", None) if b else None
            adate = getattr(a, "date_display", None) if a else None
            bplace = getattr(b, "place_token", None) if b else None
            aplace = getattr(a, "place_token", None) if a else None
            bq = getattr(b, "qualifier", None) if b else None
            aq = getattr(a, "qualifier", None) if a else None
            if (bdate, bplace, bq, b is None) == (adate, aplace, aq, a is None):
                continue

            if bdate != adate and bplace == aplace and bq == aq:
                likely = "date value changed"
            elif bplace != aplace and bdate == adate and bq == aq:
                likely = "place reference changed"
            elif bq != aq and bdate == adate and bplace == aplace:
                likely = "date qualifier changed"
            elif b is None:
                likely = "event observation added"
            elif a is None:
                likely = "event observation removed"
            else:
                likely = "multiple decoded event properties changed"

            deltas.append(
                DecodedEventDelta(
                    person_id=person_id,
                    person_name=(
                        getattr(a, "person_name", None)
                        or getattr(b, "person_name", None)
                        or f"Person {person_id}"
                    ),
                    before_date=bdate,
                    after_date=adate,
                    before_place=bplace,
                    after_place=aplace,
                    before_qualifier=bq,
                    after_qualifier=aq,
                    before_record_offset=getattr(b, "record_offset", None) if b else None,
                    after_record_offset=getattr(a, "record_offset", None) if a else None,
                    likely_change=likely,
                )
            )
    return deltas


def _structural_deltas(before_path: str | Path, after_path: str | Path):
    """Reuse Build 13 structural comparison when available."""
    try:
        from .semantic_probe import snapshot_package, compare_snapshots
    except Exception:
        return (), ()
    try:
        result = compare_snapshots(
            snapshot_package(before_path),
            snapshot_package(after_path),
            probe_id="build14-overlay",
            semantic_label="structural overlay",
        )
    except Exception:
        return (), ()

    classes = tuple(
        (item.class_id, item.before_count, item.after_count, item.delta)
        for item in result.class_deltas
    )
    edges = tuple(
        (
            item.source_class_id,
            item.target_class_id,
            item.before_count,
            item.after_count,
            item.delta,
        )
        for item in result.edge_deltas
    )
    return classes, edges


def compare_packages_differential(
    before_path: str | Path,
    after_path: str | Path,
    *,
    declared_change: str,
) -> DifferentialResult:
    before_main = _main_data_path(before_path)
    after_main = _main_data_path(after_path)
    before = before_main.read_bytes()
    after = after_main.read_bytes()
    spans = byte_differences(before, after)
    event_deltas = decoded_event_differences(before_path, after_path)
    class_deltas, edge_deltas = _structural_deltas(before_path, after_path)

    return DifferentialResult(
        declared_change=declared_change,
        before_path=str(Path(before_path).expanduser()),
        after_path=str(Path(after_path).expanduser()),
        before_hash=_digest(before),
        after_hash=_digest(after),
        before_size=len(before),
        after_size=len(after),
        byte_spans=tuple(spans),
        changed_before_bytes=sum(item.before_length for item in spans),
        changed_after_bytes=sum(item.after_length for item in spans),
        decoded_event_deltas=tuple(event_deltas),
        class_deltas=tuple(class_deltas),
        edge_deltas=tuple(edge_deltas),
    )


def person_differential(result: DifferentialResult, person_id: int) -> PersonDifferential | None:
    events = [item for item in result.decoded_event_deltas if item.person_id == person_id]
    if not events:
        return None

    offsets = [
        value
        for item in events
        for value in (item.before_record_offset, item.after_record_offset)
        if value is not None
    ]
    if offsets:
        low = min(offsets) - 1024
        high = max(offsets) + 16384
        spans = [
            span for span in result.byte_spans
            if (span.before_end >= low and span.before_start <= high)
            or (span.after_end >= low and span.after_start <= high)
        ]
    else:
        spans = list(result.byte_spans)

    return PersonDifferential(
        person_id=person_id,
        person_name=events[0].person_name,
        event_deltas=tuple(events),
        nearby_byte_spans=tuple(spans),
    )


def result_document(result: DifferentialResult) -> dict:
    return {
        "schema": "reunion-companion.differential-semantic-verification.v1",
        "phase": "Phase 2 - Semantic Discovery",
        "build": 14,
        "declared_change": result.declared_change,
        "before_path": result.before_path,
        "after_path": result.after_path,
        "before_hash": result.before_hash,
        "after_hash": result.after_hash,
        "before_size": result.before_size,
        "after_size": result.after_size,
        "raw_changed": result.raw_changed,
        "structure_changed": result.structure_changed,
        "changed_before_bytes": result.changed_before_bytes,
        "changed_after_bytes": result.changed_after_bytes,
        "byte_spans": [
            {
                "tag": item.tag,
                "before_start": item.before_start,
                "before_end": item.before_end,
                "after_start": item.after_start,
                "after_end": item.after_end,
                "before_hex": item.before_hex,
                "after_hex": item.after_hex,
                "before_ascii": item.before_ascii,
                "after_ascii": item.after_ascii,
            }
            for item in result.byte_spans
        ],
        "decoded_event_deltas": [
            {
                "person_id": item.person_id,
                "person_name": item.person_name,
                "before_date": item.before_date,
                "after_date": item.after_date,
                "before_place": item.before_place,
                "after_place": item.after_place,
                "before_qualifier": item.before_qualifier,
                "after_qualifier": item.after_qualifier,
                "likely_change": item.likely_change,
            }
            for item in result.decoded_event_deltas
        ],
        "class_deltas": [
            {
                "class_id": class_id,
                "before_count": before,
                "after_count": after,
                "delta": delta,
            }
            for class_id, before, after, delta in result.class_deltas
        ],
        "edge_deltas": [
            {
                "source": source,
                "target": target,
                "before_count": before,
                "after_count": after,
                "delta": delta,
            }
            for source, target, before, after, delta in result.edge_deltas
        ],
    }
