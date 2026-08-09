from reunion_companion.discovery.event_scanner import EventObservation
from reunion_companion.discovery.object_boundary import (
    boundary_signatures,
    build_person_boundary_map,
    candidate_boundaries,
    corpus_summary,
    transition_signatures,
)


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


def _sample_raw() -> bytes:
    raw = bytearray(300)
    raw[64:70] = bytes.fromhex("0A 00 08 00 00 00")
    # candidate block 1
    raw[96:100] = bytes.fromhex("06 00 00 00")
    raw[104:110] = bytes.fromhex("0A 00 08 00 00 00")
    # candidate block 2
    raw[160:164] = bytes.fromhex("06 00 00 00")
    raw[168:174] = bytes.fromhex("0A 00 08 00 00 00")
    return bytes(raw)


def test_candidate_boundaries_find_repeated_structural_markers() -> None:
    boundaries = candidate_boundaries(_obs(1, _sample_raw()), minimum_score=0.35)
    offsets = [item.relative_offset for item in boundaries]
    assert 32 in offsets
    assert 96 in offsets


def test_build_person_boundary_map() -> None:
    mapping = build_person_boundary_map(_obs(1, _sample_raw()))
    assert mapping.person_id == 1
    assert len(mapping.boundaries) >= 2
    assert len(mapping.blocks) >= 2


def test_boundary_signatures_and_transitions() -> None:
    observations = [_obs(i, _sample_raw()) for i in range(30)]
    signatures = boundary_signatures(observations)
    transitions = transition_signatures(observations)
    assert signatures
    assert signatures[0].count >= 30
    assert transitions


def test_corpus_summary() -> None:
    observations = [_obs(i, _sample_raw()) for i in range(10)]
    summary = corpus_summary(observations)
    assert summary.observations == 10
    assert summary.total_boundaries >= 20
