from pathlib import Path

from reunion_companion.discovery.semantic_probe import (
    ProbeSnapshot,
    aggregate_evidence,
    compare_snapshots,
    evidence_document,
)


def _snapshot(path: str, *, classes, edges=(), objects=10, observations=3):
    return ProbeSnapshot(
        package_path=path,
        package_hash=path,
        observations=observations,
        structural_objects=objects,
        object_classes=len(classes),
        class_counts=tuple(sorted(classes.items())),
        edge_counts=tuple(edges),
    )


def test_compare_snapshots_class_and_edge_deltas() -> None:
    before = _snapshot(
        "before",
        classes={"OC-A": 2, "OC-B": 1},
        edges=(("OC-A", "OC-B", 1),),
    )
    after = _snapshot(
        "after",
        classes={"OC-A": 2, "OC-B": 1, "OC-X": 1},
        edges=(("OC-A", "OC-X", 1), ("OC-X", "OC-B", 1)),
        objects=11,
    )
    result = compare_snapshots(
        before,
        after,
        probe_id="occupation-01",
        semantic_label="Occupation",
    )
    assert result.object_delta == 1
    assert any(item.class_id == "OC-X" and item.delta == 1 for item in result.class_deltas)
    assert result.edge_deltas


def test_aggregate_evidence_promotes_repeatable_class() -> None:
    results = []
    for index in range(3):
        before = _snapshot(f"before-{index}", classes={"OC-A": 1})
        after = _snapshot(f"after-{index}", classes={"OC-A": 1, "OC-X": 1}, objects=11)
        results.append(
            compare_snapshots(
                before,
                after,
                probe_id=f"occupation-{index}",
                semantic_label="Occupation",
            )
        )
    evidence = aggregate_evidence(results)
    target = next(item for item in evidence if item.class_id == "OC-X")
    assert target.support == 3
    assert target.contradictions == 0
    assert target.status == "VERIFIED"


def test_evidence_contradiction_blocks_verification() -> None:
    results = []
    for index in range(2):
        results.append(
            compare_snapshots(
                _snapshot(f"b{index}", classes={"OC-A": 1}),
                _snapshot(f"a{index}", classes={"OC-A": 1, "OC-X": 1}, objects=11),
                probe_id=f"note-{index}",
                semantic_label="General Note",
            )
        )
    results.append(
        compare_snapshots(
            _snapshot("b2", classes={"OC-A": 1, "OC-X": 1}),
            _snapshot("a2", classes={"OC-A": 1}, objects=9),
            probe_id="note-2",
            semantic_label="General Note",
        )
    )
    evidence = aggregate_evidence(results)
    target = next(item for item in evidence if item.class_id == "OC-X")
    assert target.contradictions == 1
    assert target.status != "VERIFIED"


def test_evidence_document_is_machine_readable() -> None:
    result = compare_snapshots(
        _snapshot("b", classes={"OC-A": 1}),
        _snapshot("a", classes={"OC-A": 1, "OC-X": 1}, objects=11),
        probe_id="birth-place-01",
        semantic_label="Birth Place",
    )
    evidence = aggregate_evidence([result])
    doc = evidence_document([result], evidence, manifest_path="/tmp/probes.json")
    assert doc["build"] == 13
    assert doc["automatic_canonical_promotion"] is False
    assert doc["results"][0]["semantic_label"] == "Birth Place"
