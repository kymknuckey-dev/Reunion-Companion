from reunion_companion.discovery.probe_report import (
    format_probe_plan,
    format_probe_result,
    format_semantic_evidence,
    manifest_markdown,
)
from reunion_companion.discovery.semantic_probe import (
    ProbePriority,
    ProbeSnapshot,
    aggregate_evidence,
    compare_snapshots,
)


def _result():
    before = ProbeSnapshot(
        "before", "b", 1, 2, 1,
        (("OC-A", 1),),
        (),
    )
    after = ProbeSnapshot(
        "after", "a", 1, 3, 2,
        (("OC-A", 1), ("OC-X", 1)),
        (("OC-A", "OC-X", 1),),
    )
    return compare_snapshots(
        before,
        after,
        probe_id="occupation-01",
        semantic_label="Occupation",
    )


def test_probe_formatters() -> None:
    result = _result()
    evidence = aggregate_evidence([result])
    plan = [
        ProbePriority(
            rank=1,
            class_id="OC-A",
            occurrences=100,
            people=80,
            centrality=1.0,
            in_degree=4,
            out_degree=5,
            score=0.9,
        )
    ]
    assert "Semantic Probe Priority Plan" in format_probe_plan(plan)
    assert "Semantic Probe — occupation-01" in format_probe_result(result)
    assert "Semantic Probe Evidence" in format_semantic_evidence(evidence)
    assert "# Semantic Probe Verification" in manifest_markdown([result], evidence)
