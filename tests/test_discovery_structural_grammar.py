from reunion_companion.discovery.event_scanner import EventObservation
from reunion_companion.discovery.structural_grammar import (
    class_sequences,
    discover_grammar_classes,
    discover_grammar_rules,
    discover_repetition_patterns,
    discover_sequence_motifs,
    grammar_summary,
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


def _raw() -> bytes:
    raw = bytearray(420)
    raw[64:70] = bytes.fromhex("0A 00 08 00 00 00")
    raw[96:100] = bytes.fromhex("06 00 00 00")
    raw[100:108] = bytes.fromhex("0B 00 16 00 EA 03 12 00")
    raw[112:118] = bytes.fromhex("0A 00 08 00 00 00")
    raw[176:180] = bytes.fromhex("06 00 00 00")
    raw[180:188] = bytes.fromhex("15 00 08 00 00 00 00 00")
    raw[192:198] = bytes.fromhex("0A 00 08 00 00 00")
    raw[256:260] = bytes.fromhex("06 00 00 00")
    raw[260:268] = bytes.fromhex("15 00 14 00 00 00 00 00")
    raw[272:278] = bytes.fromhex("0A 00 08 00 00 00")
    return bytes(raw)


def test_discover_grammar_classes() -> None:
    observations = [_obs(i, _raw()) for i in range(20)]
    classes, mapping = discover_grammar_classes(observations)
    assert classes
    assert mapping
    assert any(item.class_key.startswith("C06:") for item in classes)


def test_class_sequences_and_rules() -> None:
    observations = [_obs(i, _raw()) for i in range(30)]
    sequences = class_sequences(observations)
    rules = discover_grammar_rules(observations)
    assert sequences
    assert rules


def test_motifs_and_repetitions() -> None:
    observations = [_obs(i, _raw()) for i in range(40)]
    motifs = discover_sequence_motifs(observations, minimum_count=20)
    repetitions = discover_repetition_patterns(observations, minimum_count=5)
    assert motifs
    assert isinstance(repetitions, list)


def test_grammar_summary() -> None:
    observations = [_obs(i, _raw()) for i in range(10)]
    summary = grammar_summary(observations)
    assert summary.observations == 10
    assert summary.grammar_classes > 0
