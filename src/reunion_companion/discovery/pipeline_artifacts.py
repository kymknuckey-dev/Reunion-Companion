from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json

@dataclass(frozen=True, slots=True)
class PipelineArtifact:
    schema: str
    build: int
    stage: str
    input_hashes: tuple
    payload_hash: str
    payload: dict

def stable_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def hash_file(path):
    return sha256(Path(path).expanduser().read_bytes()).hexdigest()

def make_artifact(build, stage, payload, input_hashes):
    return PipelineArtifact(
        "reunion-companion.discovery-artifact.v1",
        build,
        stage,
        tuple(sorted(input_hashes.items())),
        sha256(stable_bytes(payload)).hexdigest(),
        payload,
    )

def artifact_document(a):
    return {
        "schema": a.schema,
        "build": a.build,
        "stage": a.stage,
        "input_hashes": dict(a.input_hashes),
        "payload_hash": a.payload_hash,
        "payload": a.payload,
    }

def write_artifact(path, a):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(artifact_document(a), indent=2, sort_keys=True), encoding="utf-8")
    return p

def read_artifact(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    a = PipelineArtifact(
        d["schema"], int(d["build"]), d["stage"],
        tuple(sorted(d.get("input_hashes", {}).items())),
        d["payload_hash"], d["payload"],
    )
    if sha256(stable_bytes(a.payload)).hexdigest() != a.payload_hash:
        raise ValueError("Artifact payload hash mismatch")
    return a
