from reunion_companion.discovery.event_scanner import EventObservation
from reunion_companion.discovery.full_capture import (
    capture_for_person,
    capture_summary,
    find_ascii_tokens,
    marker_relative_hexdump,
    rank_capture_candidates,
    repeated_sequences,
)


def _obs(person_id: int, raw: bytes, *, marker=64, length=1000, place=None):
    return EventObservation(
        person_id=person_id,
        person_name=f"Person {person_id}",
        record_offset=0,
        record_length=length,
        marker_offset=marker,
        raw_date_offset=marker + 7,
        date_display="1 Jan 1900",
        qualifier=0,
        place_token=place,
        memo_candidate=False,
        signature="sig",
        context_hex=raw[max(0, marker-24):marker+24].hex(" "),
        capture_start=0,
        capture_end=len(raw),
        capture_hex=raw.hex(" "),
        capture_truncated_left=False,
        capture_truncated_right=False,
    )


def test_capture_summary() -> None:
    summary = capture_summary([
        _obs(1, bytes(200), length=500),
        _obs(2, bytes(300), length=600),
    ])
    assert summary.observations == 2
    assert summary.capture_length_min == 200
    assert summary.capture_length_max == 300


def test_find_ascii_tokens() -> None:
    raw = bytearray(200)
    raw[80:90] = b"[[pt:123]]"
    tokens = find_ascii_tokens([_obs(1, bytes(raw), marker=64, place="[[pt:123]]")])
    assert tokens[0].token == "[[pt:123]]"
    assert tokens[0].sample_offsets == (16,)


def test_repeated_sequences() -> None:
    raw = bytearray(200)
    raw[80:84] = b"ABCD"
    observations = [_obs(i, bytes(raw), marker=64) for i in range(30)]
    sequences = repeated_sequences(
        observations,
        width=4,
        minimum_count=25,
        relative_start=16,
        relative_end=20,
    )
    assert sequences[0].sequence_hex == "41 42 43 44"
    assert sequences[0].relative_offset == 16


def test_rank_and_lookup() -> None:
    values = [
        _obs(1, bytes(100), length=100),
        _obs(2, bytes(200), length=500),
    ]
    assert rank_capture_candidates(values)[0].person_id == 2
    assert capture_for_person(values, 1).person_id == 1


def test_marker_relative_hexdump() -> None:
    raw = bytes(range(100))
    output = marker_relative_hexdump(_obs(1, raw, marker=64), max_bytes=32)
    assert "-00064" in output
