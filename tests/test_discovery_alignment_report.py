from reunion_companion.discovery.alignment_report import (
    alignment_markdown,
    format_alignment_edges,
    format_alignment_profile,
    format_alignment_summary,
    format_cooccurrence,
    format_object_families,
    format_object_graph,
    format_person_path,
    object_graph_dot,
)
from reunion_companion.discovery.event_scanner import EventObservation
from reunion_companion.discovery.semantic_alignment import (
    alignment_edges,
    alignment_profile,
    alignment_summary,
    cooccurrence_pairs,
    object_families,
    object_graph,
    person_object_path,
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


def test_alignment_formatters() -> None:
    observations = [_obs(i) for i in range(30)]
    summary = alignment_summary(observations)
    nodes, edges = object_graph(observations)
    families = object_families(observations)
    pairs = cooccurrence_pairs(observations)
    profile = alignment_profile(observations, edges[0].source_class_id)
    path = person_object_path(observations, 1)

    assert "Semantic Alignment Summary" in format_alignment_summary(summary)
    assert "Strongest Object-Class Alignments" in format_alignment_edges(edges)
    assert "Alignment Profile" in format_alignment_profile(profile)
    assert "Object-Class Graph" in format_object_graph(nodes)
    assert "Object-Class Co-occurrence" in format_cooccurrence(pairs)
    assert "Structural Object Families" in format_object_families(families)
    assert "Aligned Object Path" in format_person_path(path)
    assert "# Semantic Alignment & Object Graph" in alignment_markdown(
        summary, nodes, edges, families, pairs
    )
    assert "digraph ReunionObjectClasses" in object_graph_dot(nodes, edges)
