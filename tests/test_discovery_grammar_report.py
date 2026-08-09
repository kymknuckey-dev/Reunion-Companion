from reunion_companion.discovery.event_scanner import EventObservation
from reunion_companion.discovery.grammar_report import (
    format_grammar_classes,
    format_grammar_rules,
    format_grammar_summary,
    format_motifs,
    format_repetitions,
    grammar_markdown,
)
from reunion_companion.discovery.structural_grammar import (
    discover_grammar_classes,
    discover_grammar_rules,
    discover_repetition_patterns,
    discover_sequence_motifs,
    grammar_summary,
)


def _obs(person_id: int) -> EventObservation:
    raw = bytearray(340)
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
    return EventObservation(
        person_id=person_id,
        person_name=f"Person {person_id}",
        record_offset=0,
        record_length=len(raw),
        marker_offset=64,
        raw_date_offset=71,
        date_display="1 Jan 1900",
        qualifier=0,
        place_token=None,
        memo_candidate=False,
        signature="sig",
        context_hex=bytes(raw[40:88]).hex(" "),
        capture_start=0,
        capture_end=len(raw),
        capture_hex=bytes(raw).hex(" "),
        capture_truncated_left=False,
        capture_truncated_right=False,
    )


def test_grammar_formatters() -> None:
    observations = [_obs(i) for i in range(30)]
    summary = grammar_summary(observations)
    classes, _ = discover_grammar_classes(observations)
    rules = discover_grammar_rules(observations)
    motifs = discover_sequence_motifs(observations, minimum_count=10)
    repetitions = discover_repetition_patterns(observations, minimum_count=5)

    assert "Object Structural Grammar Summary" in format_grammar_summary(summary)
    assert "Neutral Grammar Classes" in format_grammar_classes(classes)
    assert "Structural Grammar Rules" in format_grammar_rules(rules)
    assert "Recurring Structural Motifs" in format_motifs(motifs)
    assert "Repeated-Class Patterns" in format_repetitions(repetitions)

    markdown = grammar_markdown(summary, classes, rules, motifs, repetitions)
    assert "# Object Structural Grammar" in markdown
