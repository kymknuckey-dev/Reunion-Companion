"""Formatting for Discovery Build 9 structural grammar."""

from __future__ import annotations

from .structural_grammar import (
    GrammarClass,
    GrammarRule,
    GrammarSummary,
    RepetitionPattern,
    SequenceMotif,
)


def format_grammar_summary(summary: GrammarSummary) -> str:
    return "\n".join(
        [
            "Object Structural Grammar Summary",
            "=================================",
            f"Observations           {summary.observations:,}",
            f"Build 8 block families {summary.block_families:,}",
            f"Grammar classes        {summary.grammar_classes:,}",
            f"Grammar rules          {summary.grammar_rules:,}",
            f"Sequence motifs        {summary.motifs:,}",
            f"Repetition patterns    {summary.repetition_patterns:,}",
            "",
            "All grammar classes are neutral structural classes.",
        ]
    )


def format_grammar_classes(classes: list[GrammarClass], *, limit: int = 50) -> str:
    lines = [
        "Neutral Grammar Classes",
        "=======================",
        "ID    Count   Families  Length range  Median   Class key        Dominant prefix",
    ]
    for item in classes[:limit]:
        lines.append(
            f"C{item.class_id:<3} "
            f"{item.total_count:>8,} "
            f"{item.member_families:>9} "
            f"{str(item.length_min)+'-'+str(item.length_max):>13} "
            f"{item.length_median:>7.1f}   "
            f"{item.class_key:<16} "
            f"{item.dominant_prefix[:35]}"
        )
        lines.append(
            f"      member families: {','.join('F'+str(v) for v in item.family_ids[:12])}"
            + (" ..." if len(item.family_ids) > 12 else "")
        )
    if len(classes) > limit:
        lines.append(f"... {len(classes) - limit} more grammar classes")
    return "\n".join(lines)


def format_grammar_rules(rules: list[GrammarRule], *, limit: int = 60) -> str:
    lines = [
        "Structural Grammar Rules",
        "========================",
        "Count    Probability   Rule",
    ]
    for item in rules[:limit]:
        lines.append(
            f"{item.count:>7,}   {item.probability:>10.1%}   "
            f"C{item.left_class_id} -> C{item.right_class_id}"
        )
    if len(rules) > limit:
        lines.append(f"... {len(rules) - limit} more rules")
    return "\n".join(lines)


def format_motifs(motifs: list[SequenceMotif], *, limit: int = 60) -> str:
    lines = [
        "Recurring Structural Motifs",
        "===========================",
        "Count   Motif                     Sample people",
    ]
    for item in motifs[:limit]:
        motif = " -> ".join(f"C{value}" for value in item.motif)
        lines.append(
            f"{item.count:>5,}   {motif:<25} "
            f"{','.join(str(v) for v in item.sample_person_ids)}"
        )
    if len(motifs) > limit:
        lines.append(f"... {len(motifs) - limit} more motifs")
    return "\n".join(lines)


def format_repetitions(repetitions: list[RepetitionPattern], *, limit: int = 40) -> str:
    lines = [
        "Repeated-Class Patterns",
        "=======================",
        "Count   Pattern      Sample people",
    ]
    for item in repetitions[:limit]:
        lines.append(
            f"{item.count:>5,}   C{item.class_id} x{item.run_length:<4} "
            f"{','.join(str(v) for v in item.sample_person_ids)}"
        )
    if len(repetitions) > limit:
        lines.append(f"... {len(repetitions) - limit} more repetition patterns")
    return "\n".join(lines)


def grammar_markdown(
    summary: GrammarSummary,
    classes: list[GrammarClass],
    rules: list[GrammarRule],
    motifs: list[SequenceMotif],
    repetitions: list[RepetitionPattern],
) -> str:
    lines = [
        "# Object Structural Grammar",
        "",
        f"- Observations: {summary.observations:,}",
        f"- Build 8 block families: {summary.block_families:,}",
        f"- Grammar classes: {summary.grammar_classes:,}",
        f"- Grammar rules: {summary.grammar_rules:,}",
        f"- Sequence motifs: {summary.motifs:,}",
        f"- Repetition patterns: {summary.repetition_patterns:,}",
        "",
        "## Grammar classes",
        "",
        "| Class | Count | Member families | Length range | Median | Key |",
        "|---:|---:|---:|---:|---:|---|",
    ]

    for item in classes:
        lines.append(
            f"| C{item.class_id} | {item.total_count} | {item.member_families} | "
            f"{item.length_min}-{item.length_max} | {item.length_median:.1f} | "
            f"`{item.class_key}` |"
        )

    lines.extend(["", "## Grammar rules", "", "| Count | Probability | Rule |", "|---:|---:|---|"])
    for item in rules:
        lines.append(
            f"| {item.count} | {item.probability:.1%} | "
            f"`C{item.left_class_id} -> C{item.right_class_id}` |"
        )

    lines.extend(["", "## Recurring motifs", "", "| Count | Motif | Sample people |", "|---:|---|---|"])
    for item in motifs:
        motif = " -> ".join(f"C{value}" for value in item.motif)
        lines.append(
            f"| {item.count} | `{motif}` | "
            f"{', '.join(str(v) for v in item.sample_person_ids)} |"
        )

    lines.extend(["", "## Repetition patterns", "", "| Count | Pattern | Sample people |", "|---:|---|---|"])
    for item in repetitions:
        lines.append(
            f"| {item.count} | `C{item.class_id} x{item.run_length}` | "
            f"{', '.join(str(v) for v in item.sample_person_ids)} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "Build 9 groups neutral Build 8 block families into higher-level grammar classes "
            "and measures recurring transitions and sequence motifs. No class is assigned a semantic Reunion meaning.",
        ]
    )

    return "\n".join(lines) + "\n"
