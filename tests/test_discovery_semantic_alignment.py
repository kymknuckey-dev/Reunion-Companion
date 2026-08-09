from reunion_companion.discovery.event_scanner import EventObservation
from reunion_companion.discovery.semantic_alignment import (
    alignment_edges,
    alignment_knowledge,
    alignment_profile,
    alignment_summary,
    cooccurrence_pairs,
    object_families,
    object_graph,
    object_sequences,
    person_object_path,
)


def _obs(person_id: int, variant: int = 0) -> EventObservation:
    raw = bytearray(420)
    raw[64:70] = bytes.fromhex("0A 00 08 00 00 00")
    raw[96:100] = bytes.fromhex("06 00 00 00")
    raw[100:108] = bytes.fromhex("0B 00 16 00 EA 03 12 00")
    raw[112:118] = bytes.fromhex("0A 00 08 00 00 00")
    raw[176:180] = bytes.fromhex("06 00 00 00")
    raw[180:188] = bytes.fromhex("15 00 08 00 00 00 00 00")
    if variant % 2 == 0:
        raw[188:192] = b"TEXT"
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


def _observations():
    return [_obs(i, i % 2) for i in range(40)]


def test_sequences_edges_and_graph() -> None:
    observations = _observations()
    assert object_sequences(observations)
    assert alignment_edges(observations)
    nodes, edges = object_graph(observations)
    assert nodes
    assert edges


def test_profile_families_and_person_path() -> None:
    observations = _observations()
    edges = alignment_edges(observations)
    profile = alignment_profile(observations, edges[0].source_class_id)
    assert profile is not None
    assert object_families(observations)
    assert person_object_path(observations, 7) is not None


def test_cooccurrence_summary_and_knowledge() -> None:
    observations = _observations()
    assert isinstance(cooccurrence_pairs(observations), list)
    summary = alignment_summary(observations)
    assert summary.observations == 40
    doc = alignment_knowledge(
        observations,
        source_package="/tmp/Probe.familyfile14",
    )
    assert doc["build"] == 12
    assert doc["semantic_labels_assigned"] is False
    assert doc["nodes"]
