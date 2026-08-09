from reunion_companion.discovery.boundary_consolidation import (
    build_consolidated_map,
    consolidate_boundaries,
    consolidation_summary,
    discover_block_families,
    discover_family_transitions,
)
from reunion_companion.discovery.event_scanner import EventObservation


def _obs(person_id: int, raw: bytes, marker: int = 64) -> EventObservation:
    return EventObservation(
        person_id=person_id,
        person_name=f"Person {person_id}",
        record_offset=0,
        record_length=len(raw),
        marker_offset=marker,
        raw_date_offset=marker + 7,
        date_display="1 Jan 1900",
        qualifier=0,
        place_token=None,
        memo_candidate=False,
        signature="sig",
        context_hex=raw[max(0, marker-24):marker+24].hex(" "),
        capture_start=0,
        capture_end=len(raw),
        capture_hex=raw.hex(" "),
        capture_truncated_left=False,
        capture_truncated_right=False,
    )


def _raw() -> bytes:
    raw = bytearray(320)
    raw[64:70] = bytes.fromhex("0A 00 08 00 00 00")
    # peer object A
    raw[96:100] = bytes.fromhex("06 00 00 00")
    raw[100:108] = bytes.fromhex("0B 00 16 00 EA 03 12 00")
    raw[112:118] = bytes.fromhex("0A 00 08 00 00 00")
    # peer object B
    raw[176:180] = bytes.fromhex("06 00 00 00")
    raw[180:188] = bytes.fromhex("15 00 08 00 00 00 00 00")
    raw[192:198] = bytes.fromhex("0A 00 08 00 00 00")
    return bytes(raw)


def test_consolidates_internal_plus4_candidates() -> None:
    observation = _obs(1, _raw())
    consolidated = consolidate_boundaries(observation)
    offsets = [item.relative_offset for item in consolidated]
    assert 32 in offsets
    assert 112 in offsets
    # internal +4 candidates should be suppressed
    assert 36 not in offsets
    assert 116 not in offsets


def test_build_consolidated_map() -> None:
    mapping = build_consolidated_map(_obs(1, _raw()))
    assert len(mapping.blocks) >= 2
    assert mapping.blocks[0].family_key.startswith("S06:")


def test_family_discovery_and_transitions() -> None:
    observations = [_obs(i, _raw()) for i in range(30)]
    families, family_ids = discover_block_families(observations)
    transitions = discover_family_transitions(observations)
    assert families
    assert family_ids
    assert transitions


def test_consolidation_summary_reduces_raw_candidates() -> None:
    observations = [_obs(i, _raw()) for i in range(10)]
    summary = consolidation_summary(observations)
    assert summary.raw_candidates >= summary.consolidated_boundaries
    assert summary.suppressed_candidates > 0
