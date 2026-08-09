"""Formatting and reports for Discovery Build 5 structural correlation."""

from __future__ import annotations

from .correlation_engine import (
    PropertyCorrelation,
    QualifierSummary,
    RankedObservation,
    StructuralMap,
)


def _byte(value: int | None) -> str:
    return "-" if value is None else f"0x{value:02X}"


def format_property_correlation(
    correlation: PropertyCorrelation,
    *,
    limit: int = 16,
) -> str:
    left = correlation.left
    right = correlation.right
    delta = correlation.record_length_mean_delta

    lines = [
        f"Structural Correlation — {correlation.property_name}",
        "=" * (25 + len(correlation.property_name)),
        "",
        f"{'':24}{left.label:>20}{right.label:>22}",
        f"{'Count':<24}{left.count:>20,}{right.count:>22,}",
    ]

    if left.record_length_mean is not None and right.record_length_mean is not None:
        lines.extend(
            [
                f"{'Mean record length':<24}{left.record_length_mean:>20.2f}{right.record_length_mean:>22.2f}",
                f"{'Median record length':<24}{left.record_length_median:>20.2f}{right.record_length_median:>22.2f}",
                f"{'Length range':<24}{str(left.record_length_min)+'-'+str(left.record_length_max):>20}"
                f"{str(right.record_length_min)+'-'+str(right.record_length_max):>22}",
                f"{'Mean length delta':<24}{delta:>20.2f}",
            ]
        )

    lines.extend(
        [
            "",
            "Strongest marker-centred byte differences",
            "----------------------------------------",
            "Offset     TV    Left common   Right common   Left share   Right share",
        ]
    )

    ranked = sorted(
        correlation.byte_correlations,
        key=lambda item: (-item.total_variation, item.relative_offset),
    )
    for item in ranked[:limit]:
        lines.append(
            f"{item.relative_offset:+5d}  "
            f"{item.total_variation:5.3f}  "
            f"{_byte(item.left_common):>11}  "
            f"{_byte(item.right_common):>12}  "
            f"{item.left_common_share:9.2f}%  "
            f"{item.right_common_share:10.2f}%"
        )

    return "\n".join(lines)


def format_qualifier_analysis(summaries: list[QualifierSummary]) -> str:
    lines = [
        "Date Qualifier Analysis",
        "=======================",
        "Qualifier    Count   Exact-like   Year-only   With place   With memo   Mean length",
    ]
    for item in summaries:
        lines.append(
            f"0x{item.qualifier:02X}"
            f"{item.count:>12,}"
            f"{item.exact_date_count:>13,}"
            f"{item.year_only_count:>12,}"
            f"{item.with_place_count:>13,}"
            f"{item.with_memo_count:>12,}"
            f"{item.record_length_mean:>14.2f}"
        )

    lines.extend(
        [
            "",
            "Semantic meaning is intentionally not assigned here.",
            "Controlled Reunion date-qualifier probes are still required.",
        ]
    )
    return "\n".join(lines)


def format_region_map(structure: StructuralMap) -> str:
    lines = [
        "Birth/Event Structural Region Map",
        "=================================",
        f"Observations: {structure.observation_count:,}",
        "",
        "Offset range    Region                    Status                           Confidence",
        "-----------------------------------------------------------------------------------",
    ]
    for region in structure.regions:
        offset = (
            f"{region.start_offset:+d}"
            if region.start_offset == region.end_offset
            else f"{region.start_offset:+d}..{region.end_offset:+d}"
        )
        lines.append(
            f"{offset:<15} {region.name:<25} {region.status:<32} {region.confidence:>8.1%}"
        )
        lines.append(f"{'':15} evidence: {region.evidence}")
    return "\n".join(lines)


def format_ranked_observations(
    title: str,
    observations: list[RankedObservation],
) -> str:
    lines = [
        title,
        "=" * len(title),
        "ID       Length  Mark   Q    Place Memo  Name / Date",
    ]
    for item in observations:
        lines.append(
            f"{item.person_id:<8}"
            f"{item.record_length:>7,} "
            f"{item.marker_offset:>5} "
            f"0x{item.qualifier:02X} "
            f"{'yes' if item.has_place else 'no':>5} "
            f"{'yes' if item.has_memo_candidate else 'no':>4}  "
            f"{item.person_name} — {item.date_display}"
        )
    return "\n".join(lines)


def format_archaeology_dashboard(
    structure: StructuralMap,
    place: PropertyCorrelation,
    memo: PropertyCorrelation,
    qualifiers: list[QualifierSummary],
) -> str:
    place_count = place.left.count
    memo_count = memo.left.count

    lines = [
        "Birth/Event Archaeology Dashboard",
        "=================================",
        f"Observations       {structure.observation_count:,}",
        f"With place         {place_count:,}",
        f"Memo candidates    {memo_count:,}",
        f"Qualifier values   {len(qualifiers):,}",
        "",
        "Knowledge Status",
        "----------------",
        "Event signature    VERIFIED",
        "Date descriptor    VERIFIED",
        "Packed date        VERIFIED",
        "Place token        VERIFIED",
        "Qualifier location VERIFIED / meaning pending",
        "Memo presence      CANDIDATE / boundary not yet captured",
        "Citations          UNKNOWN",
        "Remaining payload  PARTIAL",
        "",
        "Important constraint",
        "--------------------",
        "Current raw observation context ends at +23 relative to the date marker.",
        "Build 5 therefore correlates structure without claiming unobserved memo/citation boundaries.",
    ]
    return "\n".join(lines)


def archaeology_markdown(
    structure: StructuralMap,
    place: PropertyCorrelation,
    memo: PropertyCorrelation,
    qualifiers: list[QualifierSummary],
) -> str:
    lines = [
        "# Birth/Event Structural Correlation",
        "",
        f"- Observations: {structure.observation_count:,}",
        f"- With place: {place.left.count:,}",
        f"- Without place: {place.right.count:,}",
        f"- Memo candidates: {memo.left.count:,}",
        f"- Without memo candidate: {memo.right.count:,}",
        "",
        "## Structural regions",
        "",
        "| Range | Region | Status | Confidence | Evidence |",
        "|---|---|---|---:|---|",
    ]
    for region in structure.regions:
        range_text = (
            f"{region.start_offset:+d}"
            if region.start_offset == region.end_offset
            else f"{region.start_offset:+d}..{region.end_offset:+d}"
        )
        evidence = region.evidence.replace("|", "\\|")
        lines.append(
            f"| `{range_text}` | {region.name} | {region.status} | "
            f"{region.confidence:.1%} | {evidence} |"
        )

    lines.extend(
        [
            "",
            "## Qualifiers",
            "",
            "| Qualifier | Count | Exact-like | Year-only | With place | Memo candidate | Mean record length |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for item in qualifiers:
        lines.append(
            f"| `0x{item.qualifier:02X}` | {item.count} | {item.exact_date_count} | "
            f"{item.year_only_count} | {item.with_place_count} | {item.with_memo_count} | "
            f"{item.record_length_mean:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "The current event scanner captures 24 bytes before and 24 bytes after the generic date marker. "
            "Place-token starts can therefore be verified, but full memo, citation, and tail boundaries are not yet observable. "
            "Build 5 records those areas as candidate/partial rather than assigning unsupported semantics.",
        ]
    )
    return "\n".join(lines) + "\n"
