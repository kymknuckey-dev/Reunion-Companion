"""Formatting for Build 6 full event capture."""

from __future__ import annotations

from .event_scanner import EventObservation
from .full_capture import (
    CaptureCandidate,
    CaptureSummary,
    RepeatedSequence,
    TokenObservation,
    marker_relative_hexdump,
)


def format_capture_summary(summary: CaptureSummary) -> str:
    return "\n".join(
        [
            "Full Event Capture Summary",
            "==========================",
            f"Observations          {summary.observations:,}",
            f"Capture length min    {summary.capture_length_min:,}",
            f"Capture length max    {summary.capture_length_max:,}",
            f"Capture length mean   {summary.capture_length_mean:.2f}",
            f"Capture length median {summary.capture_length_median:.2f}",
            f"Truncated on left     {summary.truncated_left:,}",
            f"Truncated on right    {summary.truncated_right:,}",
        ]
    )


def format_tokens(tokens: list[TokenObservation], *, limit: int = 30) -> str:
    lines = [
        "ASCII Token Inventory",
        "=====================",
        "Count   Token                 Sample people     Relative offsets",
    ]
    for item in tokens[:limit]:
        lines.append(
            f"{item.count:>5,}   {item.token:<20} "
            f"{','.join(str(v) for v in item.sample_person_ids):<17} "
            f"{','.join(str(v) for v in item.sample_offsets)}"
        )
    if len(tokens) > limit:
        lines.append(f"... {len(tokens) - limit} more tokens")
    return "\n".join(lines)


def format_repeated_sequences(
    sequences: list[RepeatedSequence],
    *,
    limit: int = 40,
) -> str:
    lines = [
        "Repeated Marker-relative Sequences",
        "==================================",
        "Count   Offset   Sequence",
    ]
    for item in sequences[:limit]:
        lines.append(
            f"{item.count:>5,}   {item.relative_offset:+6d}   {item.sequence_hex}"
        )
    if len(sequences) > limit:
        lines.append(f"... {len(sequences) - limit} more sequences")
    return "\n".join(lines)


def format_capture_candidates(
    title: str,
    candidates: list[CaptureCandidate],
) -> str:
    lines = [
        title,
        "=" * len(title),
        "ID       RecLen  CapLen  Mark   Q    Place Memo  Name / Date",
    ]
    for item in candidates:
        lines.append(
            f"{item.person_id:<8}"
            f"{item.record_length:>7,} "
            f"{item.capture_length:>7,} "
            f"{item.marker_offset:>5} "
            f"0x{item.qualifier:02X} "
            f"{'yes' if item.has_place else 'no':>5} "
            f"{'yes' if item.memo_candidate else 'no':>4}  "
            f"{item.person_name} — {item.date_display}"
        )
    return "\n".join(lines)


def format_capture_person(observation: EventObservation, *, max_bytes: int = 512) -> str:
    return "\n".join(
        [
            f"Full Event Capture — Person {observation.person_id}",
            "=" * 42,
            f"Name             {observation.person_name}",
            f"Date             {observation.date_display}",
            f"Record length    {observation.record_length:,}",
            f"Marker offset    {observation.marker_offset:,}",
            f"Capture start    {observation.capture_start:,}",
            f"Capture end      {observation.capture_end:,}",
            f"Capture length   {observation.capture_length:,}",
            f"Left truncated   {'yes' if observation.capture_truncated_left else 'no'}",
            f"Right truncated  {'yes' if observation.capture_truncated_right else 'no'}",
            f"Place token      {observation.place_token or '-'}",
            f"Memo candidate   {'yes' if observation.memo_candidate else 'no'}",
            "",
            "Marker-relative hexdump",
            "-----------------------",
            marker_relative_hexdump(observation, max_bytes=max_bytes),
        ]
    )


def capture_markdown(
    summary: CaptureSummary,
    tokens: list[TokenObservation],
    sequences: list[RepeatedSequence],
) -> str:
    lines = [
        "# Full Event Capture Analysis",
        "",
        f"- Observations: {summary.observations:,}",
        f"- Capture length: {summary.capture_length_min:,}–{summary.capture_length_max:,}",
        f"- Mean capture length: {summary.capture_length_mean:.2f}",
        f"- Right-truncated captures: {summary.truncated_right:,}",
        "",
        "## ASCII tokens",
        "",
        "| Count | Token | Sample people | Relative offsets |",
        "|---:|---|---|---|",
    ]
    for item in tokens:
        lines.append(
            f"| {item.count} | `{item.token}` | "
            f"{', '.join(str(v) for v in item.sample_person_ids)} | "
            f"{', '.join(str(v) for v in item.sample_offsets)} |"
        )

    lines.extend(
        [
            "",
            "## Repeated marker-relative sequences",
            "",
            "| Count | Relative offset | Sequence |",
            "|---:|---:|---|",
        ]
    )
    for item in sequences:
        lines.append(
            f"| {item.count} | {item.relative_offset:+d} | `{item.sequence_hex}` |"
        )
    return "\n".join(lines) + "\n"
