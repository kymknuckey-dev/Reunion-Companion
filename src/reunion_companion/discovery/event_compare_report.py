"""Formatting for the Discovery Build 4 Event Comparison Engine."""

from __future__ import annotations

from .event_compare import EventComparison, EventComparisonReport, EventLayout
from .event_scanner import EventObservation


def format_event_comparison(report: EventComparisonReport, *, limit: int = 30) -> str:
    lines = [
        "Event Structure Comparison",
        "==========================",
        f"Observations      {report.observation_count:>10,}",
        f"Layouts           {len(report.layouts):>10,}",
        "",
        "Observed Layouts",
        "----------------",
    ]

    if not report.layouts:
        lines.append("(none)")
        return "\n".join(lines)

    for layout in report.layouts[:limit]:
        lines.extend(
            [
                f"Layout {layout.layout_id}",
                f"  count          {layout.count:,}",
                f"  signature      {layout.key.signature or '(empty)'}",
                f"  place          {'yes' if layout.has_place else 'no'}",
                f"  memo candidate {'yes' if layout.has_memo_candidate else 'no'}",
                f"  qualifier      0x{layout.key.qualifier:02X}",
                f"  record length  {layout.record_length_min:,}-{layout.record_length_max:,} "
                f"(mean {layout.record_length_mean:.1f})",
                f"  marker offset  {layout.marker_offset_min:,}-{layout.marker_offset_max:,}",
                f"  sample people  {', '.join(str(v) for v in layout.sample_person_ids)}",
                f"  sample dates   {'; '.join(layout.sample_dates)}",
                "",
            ]
        )

    if len(report.layouts) > limit:
        lines.append(f"... {len(report.layouts) - limit} more layouts")

    return "\n".join(lines).rstrip()


def format_layout(layout: EventLayout) -> str:
    return "\n".join(
        [
            f"Event Layout {layout.layout_id}",
            "=" * (13 + len(str(layout.layout_id))),
            f"Occurrences       {layout.count:,}",
            f"Signature         {layout.key.signature or '(empty)'}",
            f"Place token       {'yes' if layout.has_place else 'no'}",
            f"Memo candidate    {'yes' if layout.has_memo_candidate else 'no'}",
            f"Qualifier         0x{layout.key.qualifier:02X}",
            f"Record length     {layout.record_length_min:,}-{layout.record_length_max:,}",
            f"Mean length       {layout.record_length_mean:.2f}",
            f"Marker offset     {layout.marker_offset_min:,}-{layout.marker_offset_max:,}",
            f"Sample IDs        {', '.join(str(v) for v in layout.sample_person_ids)}",
            f"Sample names      {'; '.join(layout.sample_names)}",
            f"Sample dates      {'; '.join(layout.sample_dates)}",
        ]
    )


def format_layout_diff(comparison: EventComparison) -> str:
    left = comparison.left
    right = comparison.right
    lines = [
        f"Event Layout Diff: {left.layout_id} vs {right.layout_id}",
        "=" * 34,
    ]

    if comparison.identical:
        lines.append("No structural differences in comparison fields.")
        return "\n".join(lines)

    lines.extend(
        [
            "",
            f"{'Field':<24} {'Layout '+str(left.layout_id):<28} {'Layout '+str(right.layout_id)}",
            "-" * 82,
        ]
    )
    for difference in comparison.differences:
        lines.append(
            f"{difference.field:<24} {difference.left:<28} {difference.right}"
        )
    return "\n".join(lines)


def format_event_lengths(
    report: EventComparisonReport,
    *,
    limit: int = 40,
) -> str:
    lines = [
        "Event Record Lengths",
        "====================",
        "Length      Count   Histogram",
    ]

    if not report.record_lengths:
        lines.append("(none)")
        return "\n".join(lines)

    visible = report.record_lengths[:limit]
    max_count = max(bucket.count for bucket in visible)
    for bucket in visible:
        bar_len = max(1, round((bucket.count / max_count) * 30))
        lines.append(f"{bucket.length:>6,} {bucket.count:>10,}   {'#' * bar_len}")

    if len(report.record_lengths) > limit:
        lines.append(f"... {len(report.record_lengths) - limit} more lengths")

    return "\n".join(lines)


def format_observation_hexdump(observation: EventObservation) -> str:
    raw = bytes.fromhex(observation.context_hex)
    marker_in_context = min(24, observation.marker_offset)

    lines = [
        f"Event Observation Hexdump — Person {observation.person_id}",
        "=" * 48,
        f"Name             {observation.person_name}",
        f"Date             {observation.date_display}",
        f"Record offset    {observation.record_offset}",
        f"Marker offset    {observation.marker_offset}",
        f"Place token      {observation.place_token or '-'}",
        f"Memo candidate   {'yes' if observation.memo_candidate else 'no'}",
        f"Signature        {observation.signature or '(empty)'}",
        "",
        "Context (relative to marker)",
        "----------------------------",
    ]

    width = 16
    for row_start in range(0, len(raw), width):
        chunk = raw[row_start : row_start + width]
        relative_offset = row_start - marker_in_context
        hex_part = " ".join(f"{byte:02X}" for byte in chunk)
        ascii_part = "".join(chr(byte) if 32 <= byte <= 126 else "." for byte in chunk)
        lines.append(
            f"{relative_offset:+05d}  {hex_part:<47}  |{ascii_part}|"
        )

    return "\n".join(lines)


def event_comparison_markdown(report: EventComparisonReport) -> str:
    lines = [
        "# Event Structure Comparison",
        "",
        f"- Observations: {report.observation_count:,}",
        f"- Layouts: {len(report.layouts):,}",
        "",
        "## Layouts",
        "",
        "| ID | Count | Place | Memo candidate | Qualifier | Record length | Marker offset | Signature |",
        "|---:|---:|:---:|:---:|---:|---:|---:|---|",
    ]

    for layout in report.layouts:
        lines.append(
            f"| {layout.layout_id} | {layout.count} | "
            f"{'yes' if layout.has_place else 'no'} | "
            f"{'yes' if layout.has_memo_candidate else 'no'} | "
            f"`0x{layout.key.qualifier:02X}` | "
            f"{layout.record_length_min}-{layout.record_length_max} | "
            f"{layout.marker_offset_min}-{layout.marker_offset_max} | "
            f"`{layout.key.signature}` |"
        )

    lines.extend(
        [
            "",
            "## Record lengths",
            "",
            "| Length | Count |",
            "|---:|---:|",
        ]
    )
    for bucket in report.record_lengths:
        lines.append(f"| {bucket.length} | {bucket.count} |")

    return "\n".join(lines) + "\n"
