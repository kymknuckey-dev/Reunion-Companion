"""Formatting for field archaeology results."""

from __future__ import annotations

from .field_archaeology import (
    ByteStat,
    FieldArchaeologyReport,
    rank_constant_bytes,
    rank_variable_bytes,
)


def _offset_label(value: int) -> str:
    return f"{value:+d}"


def format_layout(report: FieldArchaeologyReport) -> str:
    lines = [
        "Birth/Event Layout Archaeology",
        "-----------------------------",
        f"Observations      {report.observation_count:>10,}",
        "",
        "Byte offsets relative to date marker",
        "------------------------------------",
        "Offset   Samples   Distinct   Common   Share",
    ]

    for stat in report.byte_stats:
        common = f"0x{stat.most_common_value:02X}"
        lines.append(
            f"{_offset_label(stat.relative_offset):>6}"
            f"{stat.sample_count:>10,}"
            f"{stat.distinct_values:>11,}"
            f"{common:>9}"
            f"{stat.most_common_percent:>8.1f}%"
        )

    return "\n".join(lines)


def format_offset(report: FieldArchaeologyReport, relative_offset: int) -> str:
    stat = report.byte_at(relative_offset)
    if stat is None:
        return f"No byte observations available at relative offset {relative_offset:+d}."

    return "\n".join(
        [
            f"Byte Offset {relative_offset:+d}",
            "-" * 20,
            f"Samples       {stat.sample_count:,}",
            f"Distinct      {stat.distinct_values:,}",
            f"Most common   0x{stat.most_common_value:02X}",
            f"Common count  {stat.most_common_count:,}",
            f"Share         {stat.most_common_percent:.2f}%",
            f"Constant      {'yes' if stat.is_constant else 'no'}",
        ]
    )


def format_unknown_fields(
    report: FieldArchaeologyReport,
    *,
    limit: int = 30,
) -> str:
    variable = rank_variable_bytes(report, minimum_samples=max(1, report.observation_count // 2))
    constant = rank_constant_bytes(report, minimum_samples=max(1, report.observation_count // 2))

    lines = [
        "Field Archaeology Candidates",
        "----------------------------",
        "",
        "High-coverage variable bytes",
        "----------------------------",
    ]

    if variable:
        for stat in variable[:limit]:
            lines.append(
                f"{stat.relative_offset:+4d}  "
                f"distinct={stat.distinct_values:<4d} "
                f"common=0x{stat.most_common_value:02X} "
                f"share={stat.most_common_percent:6.2f}% "
                f"samples={stat.sample_count:,}"
            )
    else:
        lines.append("(none)")

    lines.extend(["", "High-coverage constant bytes", "----------------------------"])
    if constant:
        for stat in constant[:limit]:
            lines.append(
                f"{stat.relative_offset:+4d}  "
                f"value=0x{stat.most_common_value:02X} "
                f"samples={stat.sample_count:,}"
            )
    else:
        lines.append("(none)")

    return "\n".join(lines)


def field_layout_markdown(report: FieldArchaeologyReport) -> str:
    lines = [
        "# Event Field Archaeology",
        "",
        f"- Observations: {report.observation_count:,}",
        "",
        "## Byte offsets relative to generic date marker",
        "",
        "| Offset | Samples | Distinct values | Most common | Share | Constant |",
        "|---:|---:|---:|---:|---:|:---:|",
    ]

    for stat in report.byte_stats:
        lines.append(
            f"| {stat.relative_offset:+d} | {stat.sample_count} | "
            f"{stat.distinct_values} | `0x{stat.most_common_value:02X}` | "
            f"{stat.most_common_percent:.2f}% | "
            f"{'yes' if stat.is_constant else 'no'} |"
        )

    lines.extend(
        [
            "",
            "## Candidate variable offsets",
            "",
            "| Offset | Distinct | Most common | Share | Samples |",
            "|---:|---:|---:|---:|---:|",
        ]
    )

    for stat in rank_variable_bytes(report):
        lines.append(
            f"| {stat.relative_offset:+d} | {stat.distinct_values} | "
            f"`0x{stat.most_common_value:02X}` | {stat.most_common_percent:.2f}% | "
            f"{stat.sample_count} |"
        )

    return "\n".join(lines) + "\n"
