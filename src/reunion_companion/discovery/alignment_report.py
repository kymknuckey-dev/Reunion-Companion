"""Formatting for Phase 2 Build 12 Semantic Alignment."""

from __future__ import annotations

from .semantic_alignment import (
    AlignmentEdge,
    AlignmentProfile,
    AlignmentSummary,
    CooccurrencePair,
    ObjectFamily,
    ObjectGraphNode,
    PersonObjectPath,
)


def format_alignment_summary(summary: AlignmentSummary) -> str:
    return "\n".join(
        [
            "Semantic Alignment Summary",
            "==========================",
            f"Source observations        {summary.observations:,}",
            f"Classified objects         {summary.classified_objects:,}",
            f"Stable object classes      {summary.object_classes:,}",
            f"Directed alignment edges   {summary.directed_edges:,}",
            f"High-confidence edges      {summary.high_confidence_edges:,}",
            f"Co-occurrence pairs        {summary.cooccurrence_pairs:,}",
            f"Structural graph families  {summary.graph_families:,}",
            "",
            "Alignment is structural/contextual evidence only.",
            "No Reunion semantic names are promoted in Build 12.",
        ]
    )


def format_alignment_edges(edges: list[AlignmentEdge], *, limit: int = 60) -> str:
    lines = [
        "Strongest Object-Class Alignments",
        "=================================",
        "Count   SrcProb  TgtProb  Lift    Conf    Edge",
    ]
    for edge in edges[:limit]:
        lines.append(
            f"{edge.count:>5,}   {edge.source_probability:>6.1%}  "
            f"{edge.target_probability:>6.1%}  {edge.lift:>6.2f}  "
            f"{edge.confidence:>6.1%}  "
            f"{edge.source_class_id} -> {edge.target_class_id}"
        )
    if len(edges) > limit:
        lines.append(f"... {len(edges)-limit} more edges")
    return "\n".join(lines)


def format_alignment_profile(profile: AlignmentProfile) -> str:
    lines = [
        f"Alignment Profile — {profile.class_id}",
        "=" * (20 + len(profile.class_id)),
        f"Occurrences       {profile.occurrences:,}",
        f"People            {profile.people:,}",
        f"Structural role   {profile.structural_role}",
        f"Best predecessor  {profile.best_predecessor or '-'}",
        f"Best successor    {profile.best_successor or '-'}",
        "",
        "Predecessors",
        "------------",
    ]
    if profile.predecessors:
        for edge in profile.predecessors[:10]:
            lines.append(
                f"- {edge.source_class_id}: {edge.count:,}, "
                f"target share {edge.target_probability:.1%}, "
                f"confidence {edge.confidence:.1%}"
            )
    else:
        lines.append("- none observed")

    lines.extend(["", "Successors", "----------"])
    if profile.successors:
        for edge in profile.successors[:10]:
            lines.append(
                f"- {edge.target_class_id}: {edge.count:,}, "
                f"source share {edge.source_probability:.1%}, "
                f"confidence {edge.confidence:.1%}"
            )
    else:
        lines.append("- none observed")

    lines.extend(["", "Co-occurring classes", "--------------------"])
    if profile.cooccurring:
        for pair in profile.cooccurring[:10]:
            other = (
                pair.right_class_id
                if pair.left_class_id == profile.class_id
                else pair.left_class_id
            )
            lines.append(
                f"- {other}: together in {pair.people_together:,} people, "
                f"Jaccard {pair.jaccard:.1%}, lift {pair.lift:.2f}"
            )
    else:
        lines.append("- none above threshold")
    return "\n".join(lines)


def format_object_graph(nodes: list[ObjectGraphNode], *, limit: int = 50) -> str:
    lines = [
        "Object-Class Graph",
        "==================",
        "Class          Occur People   InWt  OutWt  InD OutD Starts Ends Centrality",
    ]
    for node in nodes[:limit]:
        lines.append(
            f"{node.class_id:<14} {node.occurrences:>5,} {node.people:>6,} "
            f"{node.in_weight:>6,} {node.out_weight:>6,} "
            f"{node.in_degree:>4} {node.out_degree:>4} "
            f"{node.start_count:>6,} {node.end_count:>4,} "
            f"{node.centrality:>10.3f}"
        )
    if len(nodes) > limit:
        lines.append(f"... {len(nodes)-limit} more nodes")
    return "\n".join(lines)


def format_cooccurrence(pairs: list[CooccurrencePair], *, limit: int = 50) -> str:
    lines = [
        "Object-Class Co-occurrence",
        "==========================",
        "Together   Jaccard  Lift    Classes",
    ]
    for pair in pairs[:limit]:
        lines.append(
            f"{pair.people_together:>8,}   {pair.jaccard:>7.1%} "
            f"{pair.lift:>6.2f}  {pair.left_class_id} + {pair.right_class_id}"
        )
    if len(pairs) > limit:
        lines.append(f"... {len(pairs)-limit} more pairs")
    return "\n".join(lines)


def format_object_families(families: list[ObjectFamily], *, limit: int = 40) -> str:
    lines = [
        "Structural Object Families",
        "==========================",
        "Family    Classes  Occurrences  People  Strongest edge  Members",
    ]
    for family in families[:limit]:
        members = ", ".join(family.class_ids[:8])
        if len(family.class_ids) > 8:
            members += " ..."
        lines.append(
            f"{family.family_id:<9} {len(family.class_ids):>7} "
            f"{family.total_occurrences:>11,} {family.people_covered:>7,} "
            f"{family.strongest_edge_count:>14,}  {members}"
        )
    if len(families) > limit:
        lines.append(f"... {len(families)-limit} more families")
    return "\n".join(lines)


def format_person_path(path: PersonObjectPath) -> str:
    return "\n".join(
        [
            f"Aligned Object Path — Person {path.person_id}",
            "=" * 40,
            f"Name: {path.person_name}",
            f"Objects: {len(path.class_ids)}",
            "",
            "Path",
            "----",
            " -> ".join(path.class_ids) if path.class_ids else "(empty)",
        ]
    )


def alignment_markdown(
    summary: AlignmentSummary,
    nodes: list[ObjectGraphNode],
    edges: list[AlignmentEdge],
    families: list[ObjectFamily],
    pairs: list[CooccurrencePair],
) -> str:
    lines = [
        "# Semantic Alignment & Object Graph",
        "",
        "## Summary",
        "",
        f"- Source observations: {summary.observations:,}",
        f"- Classified objects: {summary.classified_objects:,}",
        f"- Stable object classes: {summary.object_classes:,}",
        f"- Directed alignment edges: {summary.directed_edges:,}",
        f"- High-confidence edges: {summary.high_confidence_edges:,}",
        f"- Co-occurrence pairs: {summary.cooccurrence_pairs:,}",
        f"- Structural graph families: {summary.graph_families:,}",
        "",
        "## Most central Object Classes",
        "",
        "| Class | Occurrences | People | In weight | Out weight | In degree | Out degree | Starts | Ends | Centrality |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for node in nodes[:100]:
        lines.append(
            f"| {node.class_id} | {node.occurrences} | {node.people} | "
            f"{node.in_weight} | {node.out_weight} | {node.in_degree} | "
            f"{node.out_degree} | {node.start_count} | {node.end_count} | "
            f"{node.centrality:.3f} |"
        )

    lines.extend(
        [
            "",
            "## Strongest directed alignments",
            "",
            "| Count | Source probability | Target probability | Lift | Confidence | Edge |",
            "|---:|---:|---:|---:|---:|---|",
        ]
    )
    for edge in edges[:250]:
        lines.append(
            f"| {edge.count} | {edge.source_probability:.1%} | "
            f"{edge.target_probability:.1%} | {edge.lift:.2f} | "
            f"{edge.confidence:.1%} | "
            f"`{edge.source_class_id} -> {edge.target_class_id}` |"
        )

    lines.extend(
        [
            "",
            "## Structural object families",
            "",
            "| Family | Classes | Occurrences | People | Strongest edge |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for family in families:
        lines.append(
            f"| {family.family_id} | {len(family.class_ids)} | "
            f"{family.total_occurrences} | {family.people_covered} | "
            f"{family.strongest_edge_count} |"
        )

    lines.extend(
        [
            "",
            "## Strongest co-occurrence pairs",
            "",
            "| Together | Jaccard | Lift | Pair |",
            "|---:|---:|---:|---|",
        ]
    )
    for pair in pairs[:250]:
        lines.append(
            f"| {pair.people_together} | {pair.jaccard:.1%} | {pair.lift:.2f} | "
            f"`{pair.left_class_id} + {pair.right_class_id}` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "Build 12 measures alignment between Build 11 structural Object Classes. "
            "Graph roles, connected Object Families and alignments describe observed "
            "topology only. They are not verified Reunion semantic field names.",
        ]
    )
    return "\n".join(lines) + "\n"


def object_graph_dot(
    nodes: list[ObjectGraphNode],
    edges: list[AlignmentEdge],
    *,
    max_nodes: int = 45,
    minimum_edge_count: int = 25,
) -> str:
    selected = {node.class_id for node in nodes[:max_nodes]}
    lines = [
        "digraph ReunionObjectClasses {",
        '  rankdir="LR";',
        '  node [shape=box];',
    ]
    for node in nodes[:max_nodes]:
        label = (
            f"{node.class_id}\\nocc={node.occurrences}\\n"
            f"cent={node.centrality:.2f}"
        )
        lines.append(f'  "{node.class_id}" [label="{label}"];')
    for edge in edges:
        if edge.count < minimum_edge_count:
            continue
        if edge.source_class_id not in selected or edge.target_class_id not in selected:
            continue
        lines.append(
            f'  "{edge.source_class_id}" -> "{edge.target_class_id}" '
            f'[label="{edge.count} / {edge.source_probability:.0%}"];'
        )
    lines.append("}")
    return "\n".join(lines) + "\n"
