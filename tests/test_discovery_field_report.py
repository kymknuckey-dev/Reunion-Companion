from reunion_companion.discovery.event_scanner import EventObservation
from reunion_companion.discovery.field_archaeology import analyse_observations
from reunion_companion.discovery.field_report import (
    field_layout_markdown,
    format_layout,
    format_offset,
    format_unknown_fields,
)


def _report():
    context = bytes([0] * 24 + [10] * 24)
    obs = EventObservation(
        person_id=1,
        person_name="Test Probe",
        record_offset=0,
        record_length=100,
        marker_offset=24,
        raw_date_offset=31,
        date_display="1 Jan 1900",
        qualifier=0,
        place_token=None,
        memo_candidate=False,
        signature="",
        context_hex=context.hex(" "),
    )
    return analyse_observations([obs])


def test_layout_formatter() -> None:
    output = format_layout(_report())
    assert "Byte offsets relative to date marker" in output
    assert "Observations" in output


def test_offset_formatter() -> None:
    output = format_offset(_report(), 0)
    assert "Byte Offset +0" in output
    assert "0x0A" in output


def test_unknown_fields_formatter() -> None:
    output = format_unknown_fields(_report())
    assert "High-coverage constant bytes" in output


def test_field_layout_markdown() -> None:
    output = field_layout_markdown(_report())
    assert "# Event Field Archaeology" in output
    assert "| +0 |" in output
