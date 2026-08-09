from reunion_companion.discovery.capture_report import (
    capture_markdown,
    format_capture_candidates,
    format_capture_summary,
    format_repeated_sequences,
    format_tokens,
)
from reunion_companion.discovery.full_capture import (
    CaptureCandidate,
    CaptureSummary,
    RepeatedSequence,
    TokenObservation,
)


def test_capture_formatters() -> None:
    summary = CaptureSummary(10, 100, 500, 250.0, 220.0, 2, 8)
    token = TokenObservation("[[pt:1]]", 5, (1, 2), (14, 14))
    sequence = RepeatedSequence("01 02 03 04", 30, 40)
    candidate = CaptureCandidate(1, "Test Probe", "1 Jan 1900", 500, 400, 64, True, False, 0)

    assert "Full Event Capture Summary" in format_capture_summary(summary)
    assert "[[pt:1]]" in format_tokens([token])
    assert "01 02 03 04" in format_repeated_sequences([sequence])
    assert "Test Probe" in format_capture_candidates("Largest", [candidate])

    markdown = capture_markdown(summary, [token], [sequence])
    assert "# Full Event Capture Analysis" in markdown
