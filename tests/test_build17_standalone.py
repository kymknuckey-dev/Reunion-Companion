from reunion_companion.discovery.pipeline_artifacts import (
    make_artifact, write_artifact, read_artifact
)
from reunion_companion.discovery.architecture_reconstruction import (
    ArchitectureComponent, ArchitectureSnapshot, architecture_document
)

def test_artifact_roundtrip(tmp_path):
    a = make_artifact(17, "x", {"b": 2, "a": 1}, {"input": "abc"})
    p = write_artifact(tmp_path / "a.json", a)
    r = read_artifact(p)
    assert r.payload == {"a": 1, "b": 2}

def test_evidence_boundary():
    c = ArchitectureComponent(
        "AC-1", "PRIMARY_CANDIDATE", "Birth Date", "birth-date",
        ("CR-1",), .95, ("probe",)
    )
    s = ArchitectureSnapshot((c,), (), 1, 0, 0, 0, 1, 1)
    class Corpus:
        residual_unknown = 3
    d = architecture_document(s, Corpus())
    assert d["evidence_boundary"]["implementation_claims_proven"] is False
    assert d["components"][0]["role"] == "PRIMARY_CANDIDATE"

def test_stage_identity():
    a = make_artifact(16, "canonical-regions", {}, {})
    assert a.build == 16
    assert a.stage == "canonical-regions"
