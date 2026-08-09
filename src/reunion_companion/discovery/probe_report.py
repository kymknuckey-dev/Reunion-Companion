"""Formatting for Phase 2 Build 13 semantic probes."""

from __future__ import annotations

from .semantic_probe import (
    ProbePriority,
    ProbeResult,
    SemanticEvidence,
)


def format_probe_plan(priorities: list[ProbePriority]) -> str:
    lines = [
        "Semantic Probe Priority Plan",
        "============================",
        "Rank  Class          Score  Occur  People  Centrality  InD  OutD",
    ]
    for item in priorities:
        lines.append(
            f"{item.rank:>4}  {item.class_id:<14} {item.score:>5.3f} "
            f"{item.occurrences:>6,} {item.people:>7,} "
            f"{item.centrality:>10.3f} {item.in_degree:>4} {item.out_degree:>5}"
        )
    lines.extend(
        [
            "",
            "Probe method",
            "------------",
            "1. Copy a small controlled Reunion family file.",
            "2. Change exactly one Reunion field or value.",
            "3. Save as a new package; do not modify the before snapshot.",
            "4. Compare before/after with `probe-compare`.",
            "5. Repeat independently before treating a semantic association as verified.",
        ]
    )
    return "\n".join(lines)


def format_probe_result(result: ProbeResult, *, limit: int = 40) -> str:
    lines = [
        f"Semantic Probe — {result.probe_id}",
        "=" * (17 + len(result.probe_id)),
        f"Declared change     {result.semantic_label}",
        f"Before              {result.before_path}",
        f"After               {result.after_path}",
        f"Observation delta   {result.observation_delta:+d}",
        f"Object delta        {result.object_delta:+d}",
        f"Unchanged           {'yes' if result.unchanged else 'no'}",
        "",
        "Changed Object Classes",
        "----------------------",
    ]
    if result.class_deltas:
        for item in result.class_deltas[:limit]:
            lines.append(
                f"{item.class_id:<14} {item.before_count:>6,} -> "
                f"{item.after_count:<6,}  delta {item.delta:+d}"
            )
        if len(result.class_deltas) > limit:
            lines.append(f"... {len(result.class_deltas)-limit} more class deltas")
    else:
        lines.append("(none)")

    lines.extend(["", "Changed Alignment Edges", "-----------------------"])
    if result.edge_deltas:
        for item in result.edge_deltas[:limit]:
            lines.append(
                f"{item.source_class_id} -> {item.target_class_id}: "
                f"{item.before_count:,} -> {item.after_count:,} "
                f"({item.delta:+d})"
            )
        if len(result.edge_deltas) > limit:
            lines.append(f"... {len(result.edge_deltas)-limit} more edge deltas")
    else:
        lines.append("(none)")

    lines.extend(
        [
            "",
            "Interpretation",
            "--------------",
            "The declared change is human-supplied probe metadata. Changed classes/edges "
            "are evidence candidates only; one comparison is not semantic verification.",
        ]
    )
    return "\n".join(lines)


def format_semantic_evidence(
    evidence: list[SemanticEvidence],
    *,
    limit: int = 80,
) -> str:
    lines = [
        "Semantic Probe Evidence",
        "=======================",
        "Status      Conf   Support  Contradict  Direction  Semantic label -> Object Class",
    ]
    for item in evidence[:limit]:
        lines.append(
            f"{item.status:<10} {item.confidence:>5.1%} "
            f"{item.support:>7} {item.contradictions:>11} "
            f"{item.direction:<9} {item.semantic_label} -> {item.class_id}"
        )
    if len(evidence) > limit:
        lines.append(f"... {len(evidence)-limit} more evidence rows")
    lines.extend(
        [
            "",
            "CANONICAL is never assigned automatically.",
            "VERIFIED requires repeated consistent controlled probes with no contradictions.",
        ]
    )
    return "\n".join(lines)


def manifest_markdown(
    results: list[ProbeResult],
    evidence: list[SemanticEvidence],
) -> str:
    lines = [
        "# Semantic Probe Verification",
        "",
        "## Probe results",
        "",
    ]
    for result in results:
        lines.extend(
            [
                f"### {result.probe_id} — {result.semantic_label}",
                "",
                f"- Before: `{result.before_path}`",
                f"- After: `{result.after_path}`",
                f"- Observation delta: {result.observation_delta:+d}",
                f"- Structural object delta: {result.object_delta:+d}",
                f"- Changed Object Classes: {len(result.class_deltas)}",
                f"- Changed alignment edges: {len(result.edge_deltas)}",
                "",
                "| Object Class | Before | After | Delta |",
                "|---|---:|---:|---:|",
            ]
        )
        for item in result.class_deltas:
            lines.append(
                f"| {item.class_id} | {item.before_count} | "
                f"{item.after_count} | {item.delta:+d} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Aggregated semantic evidence",
            "",
            "| Status | Confidence | Semantic label | Object Class | Direction | Support | Contradictions |",
            "|---|---:|---|---|---|---:|---:|",
        ]
    )
    for item in evidence:
        lines.append(
            f"| {item.status} | {item.confidence:.1%} | {item.semantic_label} | "
            f"{item.class_id} | {item.direction} | {item.support} | "
            f"{item.contradictions} |"
        )

    lines.extend(
        [
            "",
            "## Evidence boundary",
            "",
            "The semantic label in each probe is the user's declared controlled edit. "
            "Build 13 correlates that edit with deterministic Object Class and edge deltas. "
            "It does not infer semantic labels from payload text alone. `CANONICAL` status is "
            "reserved for explicit human promotion after independent verification.",
        ]
    )
    return "\n".join(lines) + "\n"
