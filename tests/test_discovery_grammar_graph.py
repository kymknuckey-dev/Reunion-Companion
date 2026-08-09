from reunion_companion.discovery.event_scanner import EventObservation
from reunion_companion.discovery.grammar_graph import (
    build_graph,
    discover_graph_motifs,
    graph_summary,
    graphviz_dot,
    hub_nodes,
    leaf_nodes,
    person_graph,
    root_nodes,
    successor_profiles,
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


def test_graph_build_and_summary() -> None:
    observations = [_obs(i) for i in range(30)]
    nodes, edges = build_graph(observations)
    summary = graph_summary(observations)
    assert nodes
    assert edges
    assert summary.nodes == len(nodes)
    assert summary.edges == len(edges)


def test_roots_leaves_hubs_and_successors() -> None:
    observations = [_obs(i) for i in range(30)]
    assert root_nodes(observations)
    assert leaf_nodes(observations)
    assert hub_nodes(observations)
    assert successor_profiles(observations)


def test_person_graph_and_dot() -> None:
    observations = [_obs(i) for i in range(30)]
    graph = person_graph(observations, 4)
    assert graph is not None
    assert graph.sequence
    dot = graphviz_dot(observations)
    assert "digraph ReunionGrammar" in dot


def test_graph_motifs() -> None:
    observations = [_obs(i) for i in range(40)]
    motifs = discover_graph_motifs(observations, minimum_count=20)
    assert motifs
