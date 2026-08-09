"""Build 24 Automated Probe Manifest & Validation Platform.

Build 24 turns the growing archaeology codebase into a repeatable platform:

Discovery Layer
    package/snapshot discovery, manifest generation, navigation probes
Knowledge Layer
    accumulated pipeline artifacts and semantic/object/navigation evidence
Validation Layer
    probe validation, regression execution, consistency checks

The core improvement is automated manifest creation from a folder of
`.familyfile14` snapshots. Build 24 never writes to Reunion packages.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import re

from .person_navigation_archaeology import scan_person_ids, analyse_manifest


@dataclass(frozen=True, slots=True)
class ProbeSnapshot:
    label: str
    package: str
    sequence: int
    changed_person_id: int | None
    changed_field: str | None


@dataclass(frozen=True, slots=True)
class ProbeManifestResult:
    folder: str
    persons: dict[int, str]
    snapshots: tuple[ProbeSnapshot, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ValidationResult:
    package: str
    package_exists: bool
    package_file_count: int
    known_person_ids_found: tuple[int, ...]
    missing_person_ids: tuple[int, ...]
    person_id_hit_count: int
    valid: bool
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RegressionResult:
    manifest: str
    snapshot_count: int
    validations: tuple[ValidationResult, ...]
    navigation_verdict: str
    navigation_reason: str
    passed: bool


def _natural_key(name: str):
    parts = re.split(r"(\d+)", name)
    return [int(x) if x.isdigit() else x.lower() for x in parts]


def _infer_sequence(name: str, fallback: int) -> int:
    nums = re.findall(r"(\d+)", name)
    return int(nums[-1]) if nums else fallback


def _infer_change_metadata(name: str):
    low = name.lower()
    person_id = None
    m = re.search(r"(?:person|p)[-_ ]?(\d+)", low)
    if m:
        person_id = int(m.group(1))
    field = None
    mapping = (
        ("birth-date", "Birth Date"),
        ("birth_date", "Birth Date"),
        ("birth date", "Birth Date"),
        ("birth-place", "Birth Place"),
        ("birth_place", "Birth Place"),
        ("birth place", "Birth Place"),
        ("research-note", "Research Note"),
        ("research_note", "Research Note"),
        ("research note", "Research Note"),
        ("occupation", "Occupation"),
        ("religion", "Religion"),
        ("education", "Education"),
        ("marriage", "Marriage"),
    )
    for token, label in mapping:
        if token in low:
            field = label
            break
    return person_id, field


def discover_probe_snapshots(folder: str | Path, persons: dict[int, str] | None = None) -> ProbeManifestResult:
    base = Path(folder).expanduser()
    if not base.is_dir():
        raise FileNotFoundError(f"Probe folder not found: {base}")

    persons = dict(persons or {1: "Test Probe", 2: "Mary Probe", 3: "Baby Probe"})
    packages = sorted(
        [p for p in base.iterdir() if p.name.endswith(".familyfile14")],
        key=lambda p: _natural_key(p.name),
    )
    if not packages:
        raise ValueError(f"No .familyfile14 packages found in: {base}")

    warnings = []
    snapshots = []
    for idx, p in enumerate(packages):
        seq = _infer_sequence(p.stem, idx)
        person_id, field = _infer_change_metadata(p.stem)
        if idx == 0:
            label = "baseline"
            person_id = None
            field = None
        else:
            label = re.sub(r"\.familyfile14$", "", p.name)
        snapshots.append(ProbeSnapshot(
            label=label,
            package=str(p.resolve()),
            sequence=seq,
            changed_person_id=person_id,
            changed_field=field,
        ))

    # Detect non-monotonic filename numbering.
    seqs = [s.sequence for s in snapshots]
    if seqs != sorted(seqs):
        warnings.append("Snapshot sequence is not monotonic after natural sorting.")

    # Warn when change metadata cannot be inferred.
    for s in snapshots[1:]:
        if s.changed_person_id is None or s.changed_field is None:
            warnings.append(f"Manual metadata may be required for snapshot: {Path(s.package).name}")

    return ProbeManifestResult(str(base.resolve()), persons, tuple(snapshots), tuple(warnings))


def manifest_document(result: ProbeManifestResult) -> dict[str, Any]:
    return {
        "schema": "reunion-companion.navigation-probe.v2",
        "generated_by": "Build 24 Automated Probe Manifest Engine",
        "persons": {str(k): v for k, v in sorted(result.persons.items())},
        "snapshots": [
            {
                "label": s.label,
                "package": s.package,
                **({"changed_person_id": s.changed_person_id} if s.changed_person_id is not None else {}),
                **({"changed_field": s.changed_field} if s.changed_field is not None else {}),
            }
            for s in result.snapshots
        ],
        "warnings": list(result.warnings),
    }


def write_manifest(folder: str | Path, output: str | Path | None = None, persons: dict[int, str] | None = None):
    result = discover_probe_snapshots(folder, persons)
    target = Path(output).expanduser() if output else Path(folder).expanduser() / "navigation_probe.json"
    target.write_text(json.dumps(manifest_document(result), indent=2), encoding="utf-8")
    return target, result


def validate_probe_package(package: str | Path, persons: dict[int, str]) -> ValidationResult:
    p = Path(package).expanduser()
    if not p.exists():
        return ValidationResult(str(p), False, 0, tuple(), tuple(sorted(persons)), 0, False, ("package missing",))

    file_count = 1 if p.is_file() else sum(1 for x in p.rglob("*") if x.is_file())
    hits, _ = scan_person_ids(p, persons)
    found = tuple(sorted({h.person_id for h in hits}))
    missing = tuple(sorted(set(persons) - set(found)))
    warnings = []
    if missing:
        warnings.append("Known Person IDs missing from raw byte scan: " + ",".join(map(str, missing)))
    valid = bool(file_count) and not missing
    return ValidationResult(
        str(p.resolve()), True, file_count, found, missing, len(hits), valid, tuple(warnings)
    )


def validate_manifest(path: str | Path):
    p = Path(path).expanduser()
    doc = json.loads(p.read_text(encoding="utf-8"))
    persons = {int(k): str(v) for k,v in doc.get("persons", {}).items()}
    snapshots = doc.get("snapshots", [])
    if not persons:
        raise ValueError("Manifest has no persons mapping.")
    if not snapshots:
        raise ValueError("Manifest has no snapshots.")

    vals = tuple(validate_probe_package(s["package"], persons) for s in snapshots)
    return vals


def run_regression(path: str | Path) -> RegressionResult:
    vals = validate_manifest(path)
    nav = analyse_manifest(path)
    passed = all(v.valid for v in vals) and nav.verdict in {"GO", "PARTIAL"}
    return RegressionResult(
        str(Path(path).expanduser().resolve()),
        len(vals),
        vals,
        nav.verdict,
        nav.verdict_reason,
        passed,
    )


def regression_document(r: RegressionResult):
    return {
        "schema":"reunion-companion.probe-regression.v1",
        "build":24,
        "manifest":r.manifest,
        "snapshot_count":r.snapshot_count,
        "passed":r.passed,
        "navigation_verdict":r.navigation_verdict,
        "navigation_reason":r.navigation_reason,
        "validations":[{
            "package":v.package,
            "package_exists":v.package_exists,
            "package_file_count":v.package_file_count,
            "known_person_ids_found":list(v.known_person_ids_found),
            "missing_person_ids":list(v.missing_person_ids),
            "person_id_hit_count":v.person_id_hit_count,
            "valid":v.valid,
            "warnings":list(v.warnings),
        } for v in r.validations]
    }
