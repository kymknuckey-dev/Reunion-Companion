"""Formatting for Build 8 boundary consolidation."""

from __future__ import annotations

from .boundary_consolidation import (
    BlockFamily,
    ConsolidatedPersonMap,
    ConsolidationSummary,
    FamilyTransition,
)


def format_consolidation_summary(summary: ConsolidationSummary) -> str:
    reduction = (
        (summary.suppressed_candidates / summary.raw_candidates * 100.0)
        if summary.raw_candidates else 0.0
    )
    return "\n".join(
        [
            "Object Boundary Consolidation Summary",
            "=====================================",
            f"Observations                {summary.observations:,}",
            f"Raw Build 7 candidates      {summary.raw_candidates:,}",
            f"Consolidated boundaries     {summary.consolidated_boundaries:,}",
            f"Suppressed internal fields  {summary.suppressed_candidates:,}",
            f"Candidate reduction         {reduction:.2f}%",
            f"Neutral block families      {summary.block_families:,}",
            f"Family transitions          {summary.family_transitions:,}",
            "",
            "Families are structural only; no semantic Reunion labels are assigned.",
        ]
    )


def format_consolidated_person(mapping: ConsolidatedPersonMap) -> str:
    lines = [
        f"Consolidated Object Map — Person {mapping.person_id}",
        "=" * 44,
        f"Name: {mapping.person_name}",
        f"Date: {mapping.date_display}",
        f"Consolidated boundaries: {len(mapping.boundaries)}",
        "",
        "Blocks",
        "------",
        "Start    End    Length  Family                  Children  Prefix / ASCII",
    ]

    for block in mapping.blocks:
        lines.append(
            f"{block.start_relative:+6d} "
            f"{block.end_relative:+6d} "
            f"{block.length:>7,}  "
            f"{block.family_key:<22} "
            f"{block.child_candidates:>8}  "
            f"{block.prefix_hex[:29]:<29} {block.ascii_preview}"
        )
    return "\n".join(lines)


def format_block_families(
    families: list[BlockFamily],
    *,
    limit: int = 50,
) -> str:
    lines = [
        "Consolidated Block Families",
        "===========================",
        "ID    Count   Length range   Median   Family key              Common words",
    ]

    for item in families[:limit]:
        words = " ".join(f"{word:04X}" for word in item.common_field_words[:6])
        lines.append(
            f"{item.family_id:>2} "
            f"{item.count:>8,} "
            f"{str(item.length_min)+'-'+str(item.length_max):>14} "
            f"{item.length_median:>8.1f}   "
            f"{item.family_key:<23} "
            f"{words}"
        )
        lines.append(
            f"     samples people={','.join(str(v) for v in item.sample_person_ids)} "
            f"offsets={','.join(str(v) for v in item.sample_offsets)}"
        )

    if len(families) > limit:
        lines.append(f"... {len(families) - limit} more families")

    return "\n".join(lines)


def format_family_transitions(
    transitions: list[FamilyTransition],
    *,
    limit: int = 50,
) -> str:
    lines = [
        "Consolidated Family Transitions",
        "===============================",
        "Count    From -> To",
    ]
    for item in transitions[:limit]:
        lines.append(
            f"{item.count:>7,}   F{item.left_family_id} -> F{item.right_family_id}"
        )
    if len(transitions) > limit:
        lines.append(f"... {len(transitions) - limit} more transitions")
    return "\n".join(lines)


def consolidation_markdown(
    summary: ConsolidationSummary,
    families: list[BlockFamily],
    transitions: list[FamilyTransition],
) -> str:
    lines = [
        "# Object Boundary Consolidation",
        "",
        f"- Observations: {summary.observations:,}",
        f"- Raw Build 7 candidates: {summary.raw_candidates:,}",
        f"- Consolidated boundaries: {summary.consolidated_boundaries:,}",
        f"- Suppressed internal-field candidates: {summary.suppressed_candidates:,}",
        f"- Neutral block families: {summary.block_families:,}",
        f"- Family transitions: {summary.family_transitions:,}",
        "",
        "## Neutral block families",
        "",
        "| ID | Count | Length range | Median | Family key | Common 16-bit words |",
        "|---:|---:|---:|---:|---|---|",
    ]

    for item in families:
        words = " ".join(f"{word:04X}" for word in item.common_field_words[:6])
        lines.append(
            f"| {item.family_id} | {item.count} | "
            f"{item.length_min}-{item.length_max} | {item.length_median:.1f} | "
            f"`{item.family_key}` | `{words}` |"
        )

    lines.extend(
        [
            "",
            "## Family transitions",
            "",
            "| Count | From | To |",
            "|---:|---:|---:|",
        ]
    )

    for item in transitions:
        lines.append(
            f"| {item.count} | F{item.left_family_id} | F{item.right_family_id} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "Build 8 merges candidate starts that behave like internal fields or payload wrappers. "
            "The resulting families are neutral structural templates only. Semantic labels remain pending controlled-probe evidence.",
        ]
    )

    return "\n".join(lines) + "\n"
