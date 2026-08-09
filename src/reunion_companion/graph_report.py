"""Formatting for Build 10 Grammar Graph Engine."""

from __future__ import annotations

from .grammar_graph import (
    GraphEdge,
    GraphMotif,
    GraphNode,
    GraphSummary,
    PersonGraph,
    SuccessorProfile,
)


def format_graph_summary(summary: GraphSummary) -> str:
    return "\n".join(
        [
            "Grammar Graph Summary",
            "=====================",
            f"Observations             {summary.observations:,}",
            f"Grammar nodes            {summary.nodes:,}",
            f"Directed edges           {summary.edges:,}",
            f"Observed root classes    {summary.roots:,}",
            f"Observed leaf classes    {summary.leaves:,}",
            f"Hub classes              {summary.hubs:,}",
            f"Mandatory successors     {summary.mandatory_successors:,}",
            f"Graph motifs             {summary.motifs:,}",
            "",
            "Graph classes remain neutral structural classes.",
        ]
    )


def _format_nodes(title: str, nodes: list[GraphNode], metric: str) -> str:
    lines = [
        title,
        "=" * len(title),
        "Class   Occur    InWt   OutWt   InDeg  OutDeg  Roots  Leaves  Hub   Key",
    ]
    for n in nodes:
        lines.append(
            f"C{n.class_id:<5} {n.occurrences:>7,} {n.in_weight:>7,} "
            f"{n.out_weight:>7,} {n.in_degree:>6} {n.out_degree:>7} "
            f"{n.root_count:>6,} {n.leaf_count:>7,} {n.hub_score:>5.2f} "
            f"{n.class_key}"
        )
    return "\n".join(lines)


def format_roots(nodes: list[GraphNode]) -> str:
    return _format_nodes("Grammar Root Classes", nodes, "root_count")


def format_leaves(nodes: list[GraphNode]) -> str:
    return _format_nodes("Grammar Leaf Classes", nodes, "leaf_count")


def format_hubs(nodes: list[GraphNode]) -> str:
    return _format_nodes("Grammar Hub Classes", nodes, "hub_score")


def format_edges(edges: list[GraphEdge], *, limit: int = 60) -> str:
    lines = [
        "Weighted Grammar Edges",
        "======================",
        "Count    Probability   Edge",
    ]
    for edge in edges[:limit]:
        lines.append(
            f"{edge.count:>7,}   {edge.probability:>10.1%}   "
            f"C{edge.source} -> C{edge.target}"
        )
    if len(edges) > limit:
        lines.append(f"... {len(edges)-limit} more edges")
    return "\n".join(lines)


def format_successors(
    profiles: list[SuccessorProfile],
    *,
    limit: int = 40,
) -> str:
    ranked = sorted(
        [p for p in profiles if p.total_outgoing],
        key=lambda p: (-p.total_outgoing, p.class_id),
    )
    lines = [
        "Successor Profiles",
        "==================",
        "Class   Outgoing   Mandatory   Top successors",
    ]
    for p in ranked[:limit]:
        mandatory = f"C{p.mandatory_successor}" if p.mandatory_successor else "-"
        top = ", ".join(
            f"C{target}:{count}/{prob:.0%}"
            for target, count, prob in p.successors[:5]
        )
        lines.append(
            f"C{p.class_id:<6} {p.total_outgoing:>8,}   "
            f"{mandatory:<9}   {top}"
        )
    return "\n".join(lines)


def format_graph_motifs(motifs: list[GraphMotif], *, limit: int = 60) -> str:
    lines = [
        "Grammar Graph Motifs",
        "====================",
        "Count   Type         Classes                    Sample people",
    ]
    for m in motifs[:limit]:
        classes = " -> ".join(f"C{x}" for x in m.classes)
        lines.append(
            f"{m.count:>5,}   {m.motif_type:<12} {classes:<26} "
            f"{','.join(str(x) for x in m.sample_person_ids)}"
        )
    if len(motifs) > limit:
        lines.append(f"... {len(motifs)-limit} more motifs")
    return "\n".join(lines)


def format_person_graph(graph: PersonGraph) -> str:
    sequence = " -> ".join(f"C{x}" for x in graph.sequence)
    nodes = ", ".join(f"C{x}" for x in graph.nodes)
    lines = [
        f"Person Grammar Graph — ID {graph.person_id}",
        "=" * 38,
        f"Sequence length: {len(graph.sequence)}",
        f"Unique nodes:    {len(graph.nodes)}",
        f"Edges:           {len(graph.edges)}",
        "",
        f"Nodes: {nodes}",
        "",
        "Sequence",
        "--------",
        sequence or "(empty)",
    ]
    return "\n".join(lines)


def graph_markdown(
    summary: GraphSummary,
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    profiles: list[SuccessorProfile],
    motifs: list[GraphMotif],
) -> str:
    lines = [
        "# Grammar Graph",
        "",
        f"- Observations: {summary.observations:,}",
        f"- Nodes: {summary.nodes:,}",
        f"- Directed edges: {summary.edges:,}",
        f"- Root classes: {summary.roots:,}",
        f"- Leaf classes: {summary.leaves:,}",
        f"- Hub classes: {summary.hubs:,}",
        f"- Mandatory successors: {summary.mandatory_successors:,}",
        f"- Graph motifs: {summary.motifs:,}",
        "",
        "## Nodes",
        "",
        "| Class | Key | Occurrences | In weight | Out weight | In degree | Out degree | Roots | Leaves | Hub score |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for n in nodes:
        lines.append(
            f"| C{n.class_id} | `{n.class_key}` | {n.occurrences} | {n.in_weight} | "
            f"{n.out_weight} | {n.in_degree} | {n.out_degree} | {n.root_count} | "
            f"{n.leaf_count} | {n.hub_score:.3f} |"
        )

    lines.extend(["", "## Edges", "", "| Count | Probability | Edge |", "|---:|---:|---|"])
    for e in edges:
        lines.append(
            f"| {e.count} | {e.probability:.1%} | `C{e.source} -> C{e.target}` |"
        )

    lines.extend(["", "## Mandatory/optional successors", "", "| Class | Mandatory | Top successors |", "|---:|---:|---|"])
    for p in profiles:
        if not p.total_outgoing:
            continue
        mandatory = f"C{p.mandatory_successor}" if p.mandatory_successor else "-"
        top = ", ".join(
            f"C{target} ({count}, {prob:.1%})"
            for target, count, prob in p.successors[:5]
        )
        lines.append(f"| C{p.class_id} | {mandatory} | {top} |")

    lines.extend(["", "## Graph motifs", "", "| Count | Type | Classes | Sample people |", "|---:|---|---|---|"])
    for m in motifs:
        classes = " -> ".join(f"C{x}" for x in m.classes)
        lines.append(
            f"| {m.count} | {m.motif_type} | `{classes}` | "
            f"{', '.join(str(x) for x in m.sample_person_ids)} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "Build 10 models neutral structural classes as a weighted directed graph. "
            "Root, leaf, hub, mandatory-successor, and motif labels describe graph behaviour only; "
            "they do not assign Reunion semantic meaning.",
        ]
    )
    return "\n".join(lines) + "\n"
