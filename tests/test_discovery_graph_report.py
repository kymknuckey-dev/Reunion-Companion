from reunion_companion.discovery.event_scanner import EventObservation
from reunion_companion.discovery.grammar_graph import (
    build_graph,
    discover_graph_motifs,
    graph_summary,
    person_graph,
    successor_profiles,
)
from reunion_companion.discovery.graph_report import (
    format_edges,
    format_graph_motifs,
    format_graph_summary,
    format_hubs,
    format_leaves,
    format_person_graph,
    format_roots,
    format_successors,
    graph_markdown,
)


def _obs(person_id: int) -> EventObservation:
    raw = bytearray(340)
    raw[64:70] = bytes.fromhex("0A 00 08 00 00 00")
    raw[96:100] = bytes.fromhex("06 00 00 00")
    raw[100:108] = bytes.fromhex("0B 00 16 00 EA 03 12 00")
    raw[112:118] = bytes.fromhex("0A 00 08 00 00 00")
    raw[176:180] = bytes.fromhex("06 00 00 00")
    raw[180:188] = bytes.fromhex("15 00 08 00 00 00 00 00")
    raw[192:198] = bytes.fromhex("0A 00 08 00 00 00")
    raw[256:260] = bytes.fromhex("06 00 00 00")
    raw[260:268] = bytes.fromhex("0B 00 14 00 00 00 00 00")
    raw[272:278] = bytes.fromhex("0A 00 08 00 00 00")
    return EventObservation(
        person_id=person_id,
        person_name=f"Person {person_id}",
        record_offset=0,
        record_length=len(raw),
        marker_offset=64,
        raw_date_offset=71,
        date_display="1 Jan 1900",
        qualifier=0,
        place_token=None,
        memo_candidate=False,
        signature="sig",
        context_hex=bytes(raw[40:88]).hex(" "),
        capture_start=0,
        capture_end=len(raw),
        capture_hex=bytes(raw).hex(" "),
        capture_truncated_left=False,
        capture_truncated_right=False,
    )


def test_graph_formatters() -> None:
    observations = [_obs(i) for i in range(30)]
    summary = graph_summary(observations)
    nodes, edges = build_graph(observations)
    profiles = successor_profiles(observations)
    motifs = discover_graph_motifs(observations, minimum_count=10)
    graph = person_graph(observations, 1)

    assert "Grammar Graph Summary" in format_graph_summary(summary)
    assert "Grammar Root Classes" in format_roots(nodes[:2])
    assert "Grammar Leaf Classes" in format_leaves(nodes[:2])
    assert "Grammar Hub Classes" in format_hubs(nodes[:2])
    assert "Weighted Grammar Edges" in format_edges(edges)
    assert "Successor Profiles" in format_successors(profiles)
    assert "Grammar Graph Motifs" in format_graph_motifs(motifs)
    assert "Person Grammar Graph" in format_person_graph(graph)
    assert "# Grammar Graph" in graph_markdown(summary, nodes, edges, profiles, motifs)
