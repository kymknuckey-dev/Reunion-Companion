"""Formatting for Build 7 candidate object-boundary discovery."""

from __future__ import annotations

from .object_boundary import (
    BoundaryCorpusSummary,
    BoundarySignature,
    PersonBoundaryMap,
    TransitionSignature,
)


def format_boundary_summary(summary: BoundaryCorpusSummary) -> str:
    return "\n".join(
        [
            "Object Boundary Scanner Summary",
            "===============================",
            f"Observations                 {summary.observations:,}",
            f"With boundary candidates     {summary.observations_with_boundaries:,}",
            f"Total boundary candidates    {summary.total_boundaries:,}",
            f"Mean candidates / record     {summary.mean_boundaries:.2f}",
            f"Median candidates / record   {summary.median_boundaries:.2f}",
            f"Unique boundary signatures   {summary.unique_boundary_signatures:,}",
            f"Unique transitions           {summary.unique_transitions:,}",
            "",
            "These are structural candidates, not semantic object labels.",
        ]
    )


def format_person_boundaries(mapping: PersonBoundaryMap) -> str:
    lines = [
        f"Object Boundary Map — Person {mapping.person_id}",
        "=" * 42,
        f"Name: {mapping.person_name}",
        f"Date: {mapping.date_display}",
        f"Boundary candidates: {len(mapping.boundaries)}",
        "",
        "Candidates",
        "----------",
        "Offset   Score   Pattern                    Evidence",
    ]

    for item in mapping.boundaries:
        reasons = "; ".join(item.reasons)
        lines.append(
            f"{item.relative_offset:+6d}   {item.score:>5.2f}   "
            f"{item.pattern_hex:<26} {reasons}"
        )

    lines.extend(
        [
            "",
            "Candidate blocks",
            "----------------",
            "Start    End    Length   Signature                              ASCII preview",
        ]
    )
    for block in mapping.blocks:
        lines.append(
            f"{block.start_relative:+6d} "
            f"{block.end_relative:+6d} "
            f"{block.length:>8,}   "
            f"{block.signature_hex:<36} "
            f"{block.ascii_preview}"
        )

    return "\n".join(lines)


def format_boundary_signatures(
    signatures: list[BoundarySignature],
    *,
    limit: int = 40,
) -> str:
    lines = [
        "Recurring Boundary Signatures",
        "=============================",
        "Count   Signature                    Sample people      Relative offsets",
    ]
    for item in signatures[:limit]:
        lines.append(
            f"{item.count:>5,}   {item.signature_hex:<28} "
            f"{','.join(str(v) for v in item.sample_person_ids):<18} "
            f"{','.join(str(v) for v in item.sample_offsets)}"
        )
    if len(signatures) > limit:
        lines.append(f"... {len(signatures) - limit} more signatures")
    return "\n".join(lines)


def format_transitions(
    transitions: list[TransitionSignature],
    *,
    limit: int = 40,
) -> str:
    lines = [
        "Recurring Candidate Object Transitions",
        "======================================",
        "Count   Left signature              -> Right signature",
    ]
    for item in transitions[:limit]:
        lines.append(
            f"{item.count:>5,}   {item.left_signature:<26} -> {item.right_signature}"
        )
    if len(transitions) > limit:
        lines.append(f"... {len(transitions) - limit} more transitions")
    return "\n".join(lines)


def boundary_markdown(
    summary: BoundaryCorpusSummary,
    signatures: list[BoundarySignature],
    transitions: list[TransitionSignature],
) -> str:
    lines = [
        "# Candidate Object Boundary Analysis",
        "",
        f"- Observations: {summary.observations:,}",
        f"- Observations with candidates: {summary.observations_with_boundaries:,}",
        f"- Total boundary candidates: {summary.total_boundaries:,}",
        f"- Unique boundary signatures: {summary.unique_boundary_signatures:,}",
        f"- Unique transitions: {summary.unique_transitions:,}",
        "",
        "## Recurring boundary signatures",
        "",
        "| Count | Signature | Sample people | Sample relative offsets |",
        "|---:|---|---|---|",
    ]

    for item in signatures:
        lines.append(
            f"| {item.count} | `{item.signature_hex}` | "
            f"{', '.join(str(v) for v in item.sample_person_ids)} | "
            f"{', '.join(str(v) for v in item.sample_offsets)} |"
        )

    lines.extend(
        [
            "",
            "## Recurring transitions",
            "",
            "| Count | Left signature | Right signature |",
            "|---:|---|---|",
        ]
    )
    for item in transitions:
        lines.append(
            f"| {item.count} | `{item.left_signature}` | `{item.right_signature}` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "Build 7 identifies candidate object starts using recurring structural patterns, "
            "nearby date descriptors, place tokens, and header-like little-endian fields. "
            "These candidates are not promoted to semantic Reunion object types until controlled probes confirm them.",
        ]
    )

    return "\n".join(lines) + "\n"
