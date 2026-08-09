from reunion_companion.discovery.boundary_report import (
    boundary_markdown,
    format_boundary_signatures,
    format_boundary_summary,
    format_person_boundaries,
    format_transitions,
)
from reunion_companion.discovery.event_scanner import EventObservation
from reunion_companion.discovery.object_boundary import (
    boundary_signatures,
    build_person_boundary_map,
    corpus_summary,
    transition_signatures,
)


def _obs() -> EventObservation:
    raw = bytearray(240)
    raw[64:70] = bytes.fromhex("0A 00 08 00 00 00")
    raw[96:100] = bytes.fromhex("06 00 00 00")
    raw[104:110] = bytes.fromhex("0A 00 08 00 00 00")
    raw[160:164] = bytes.fromhex("06 00 00 00")
    raw[168:174] = bytes.fromhex("0A 00 08 00 00 00")
    return EventObservation(
        person_id=1,
        person_name="Test Probe",
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


def test_boundary_formatters() -> None:
    observations = [_obs()]
    summary = corpus_summary(observations)
    mapping = build_person_boundary_map(observations[0])
    signatures = boundary_signatures(observations)
    transitions = transition_signatures(observations)

    assert "Object Boundary Scanner Summary" in format_boundary_summary(summary)
    assert "Candidate blocks" in format_person_boundaries(mapping)
    assert "Recurring Boundary Signatures" in format_boundary_signatures(signatures)
    assert "Recurring Candidate Object Transitions" in format_transitions(transitions)

    markdown = boundary_markdown(summary, signatures, transitions)
    assert "# Candidate Object Boundary Analysis" in markdown
