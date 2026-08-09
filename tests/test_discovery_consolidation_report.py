from reunion_companion.discovery.boundary_consolidation import (
    build_consolidated_map,
    consolidation_summary,
    discover_block_families,
    discover_family_transitions,
)
from reunion_companion.discovery.consolidation_report import (
    consolidation_markdown,
    format_block_families,
    format_consolidated_person,
    format_consolidation_summary,
    format_family_transitions,
)
from reunion_companion.discovery.event_scanner import EventObservation


def _obs() -> EventObservation:
    raw = bytearray(260)
    raw[64:70] = bytes.fromhex("0A 00 08 00 00 00")
    raw[96:100] = bytes.fromhex("06 00 00 00")
    raw[100:108] = bytes.fromhex("0B 00 16 00 EA 03 12 00")
    raw[112:118] = bytes.fromhex("0A 00 08 00 00 00")
    raw[176:180] = bytes.fromhex("06 00 00 00")
    raw[180:188] = bytes.fromhex("15 00 08 00 00 00 00 00")
    raw[192:198] = bytes.fromhex("0A 00 08 00 00 00")
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


def test_consolidation_formatters() -> None:
    observations = [_obs()]
    summary = consolidation_summary(observations)
    mapping = build_consolidated_map(observations[0])
    families, _ = discover_block_families(observations)
    transitions = discover_family_transitions(observations)

    assert "Object Boundary Consolidation Summary" in format_consolidation_summary(summary)
    assert "Consolidated Object Map" in format_consolidated_person(mapping)
    assert "Consolidated Block Families" in format_block_families(families)
    assert "Consolidated Family Transitions" in format_family_transitions(transitions)

    markdown = consolidation_markdown(summary, families, transitions)
    assert "# Object Boundary Consolidation" in markdown
