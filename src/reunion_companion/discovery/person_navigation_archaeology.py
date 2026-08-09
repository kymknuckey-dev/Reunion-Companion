"""Build 23 Person Index & Navigation Archaeology Engine.

Build 23 reverses the earlier abstraction direction. Rather than infer owner
identity from semantic regions, it starts with known Reunion Person IDs and
searches the physical package/navigation path.

Primary evidence:
- exact byte occurrences of known Person IDs across package files;
- recurring ordered ID sequences (e.g. 1,2,3) at plausible strides;
- changed files/runs across controlled snapshot edits;
- whether the changed Person ID occurs near a changed run;
- files whose size/change behaviour resembles an append/update Change Log;
- filenames/tokens suggestive of log/history/change/navigation/index structures.

This engine is read-only. A hit is a candidate reference, not proof of meaning.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
from typing import Any
import json
import struct

from .pipeline_artifacts import make_artifact, write_artifact


ENCODINGS = (
    ("u8", 1, "little"),
    ("u16le", 2, "little"),
    ("u16be", 2, "big"),
    ("u32le", 4, "little"),
    ("u32be", 4, "big"),
    ("u64le", 8, "little"),
    ("u64be", 8, "big"),
)

NAME_HINTS = ("change", "log", "history", "undo", "journal", "index", "person", "people", "record", "nav")


@dataclass(frozen=True, slots=True)
class IDHit:
    person_id: int
    person_name: str
    file: str
    offset: int
    encoding: str
    width: int
    context_hex: str


@dataclass(frozen=True, slots=True)
class IndexCandidate:
    file: str
    encoding: str
    stride: int
    start_offset: int
    matched_ids: tuple[int, ...]
    score: float
    evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ChangedRun:
    file: str
    start: int
    before_end: int
    after_end: int
    before_len: int
    after_len: int
    nearby_person_ids: tuple[int, ...]
    name_hint: bool


@dataclass(frozen=True, slots=True)
class SnapshotDelta:
    label: str
    before: str
    after: str
    changed_person_id: int | None
    changed_field: str | None
    changed_files: tuple[str, ...]
    runs: tuple[ChangedRun, ...]


@dataclass(frozen=True, slots=True)
class NavigationSnapshot:
    hits: tuple[IDHit, ...]
    index_candidates: tuple[IndexCandidate, ...]
    deltas: tuple[SnapshotDelta, ...]
    candidate_change_log_files: tuple[str, ...]
    package_files_scanned: int
    verdict: str
    verdict_reason: str


def _files(package: Path) -> dict[str, bytes]:
    package = Path(package)
    if package.is_file():
        return {package.name: package.read_bytes()}
    result = {}
    for p in sorted(package.rglob("*")):
        if p.is_file():
            try:
                result[str(p.relative_to(package))] = p.read_bytes()
            except OSError:
                pass
    return result


def _encode(value: int, width: int, endian: str) -> bytes:
    if value < 0 or value >= 1 << (width * 8):
        return b""
    return int(value).to_bytes(width, endian, signed=False)


def scan_person_ids(package: str | Path, persons: dict[int, str], max_hits_per_key: int = 5000):
    blobs = _files(Path(package))
    hits = []
    for rel, data in blobs.items():
        for pid, name in persons.items():
            for enc, width, endian in ENCODINGS:
                needle = _encode(pid, width, endian)
                if not needle:
                    continue
                start = 0
                count = 0
                while count < max_hits_per_key:
                    pos = data.find(needle, start)
                    if pos < 0:
                        break
                    lo = max(0, pos - 12)
                    hi = min(len(data), pos + width + 12)
                    hits.append(IDHit(
                        pid, name, rel, pos, enc, width,
                        data[lo:hi].hex(" ")
                    ))
                    count += 1
                    start = pos + 1
    return tuple(hits), blobs


def find_index_candidates(blobs: dict[str, bytes], persons: dict[int, str]):
    ids = sorted(persons)
    if len(ids) < 2:
        return tuple()
    candidates = {}
    # Search plausible fixed-width/stride tables containing the known IDs in order.
    for rel, data in blobs.items():
        for enc, width, endian in ENCODINGS:
            encoded = {pid: _encode(pid, width, endian) for pid in ids}
            for stride in (width, width+1, width+2, width+4, 8, 12, 16, 24, 32, 48, 64):
                if stride < width:
                    continue
                first = encoded[ids[0]]
                start = 0
                while True:
                    pos = data.find(first, start)
                    if pos < 0:
                        break
                    matched = []
                    for i, pid in enumerate(ids):
                        at = pos + i * stride
                        if at + width <= len(data) and data[at:at+width] == encoded[pid]:
                            matched.append(pid)
                        else:
                            break
                    if len(matched) >= 2:
                        hint = any(x in rel.lower() for x in NAME_HINTS)
                        score = min(.99, .45 + .12*len(matched) + (.10 if hint else 0) + (.08 if stride in (width,8,16,32) else 0))
                        key = (rel, enc, stride, pos, tuple(matched))
                        candidates[key] = IndexCandidate(
                            rel, enc, stride, pos, tuple(matched), score,
                            (
                                f"ordered known IDs={','.join(map(str, matched))}",
                                f"fixed stride={stride}",
                                f"filename-hint={hint}",
                            )
                        )
                    start = pos + 1
    return tuple(sorted(candidates.values(), key=lambda x: (-x.score, x.file, x.start_offset)))


def _changed_runs(before: bytes, after: bytes, merge_gap: int = 16):
    n = min(len(before), len(after))
    diffs = [i for i in range(n) if before[i] != after[i]]
    runs = []
    if diffs:
        s = prev = diffs[0]
        for i in diffs[1:]:
            if i - prev <= merge_gap:
                prev = i
            else:
                runs.append((s, prev+1, prev+1))
                s = prev = i
        runs.append((s, prev+1, prev+1))
    if len(before) != len(after):
        start = n
        runs.append((start, len(before), len(after)))
    return runs


def _nearby_ids(data: bytes, start: int, end: int, persons: dict[int, str], radius: int = 96):
    lo = max(0, start-radius)
    hi = min(len(data), end+radius)
    chunk = data[lo:hi]
    found = set()
    for pid in persons:
        for _, width, endian in ENCODINGS:
            needle = _encode(pid, width, endian)
            if needle and needle in chunk:
                found.add(pid)
    return tuple(sorted(found))


def compare_packages(before_package: str | Path, after_package: str | Path, persons: dict[int, str],
                     label: str = "", changed_person_id=None, changed_field=None):
    before = _files(Path(before_package))
    after = _files(Path(after_package))
    all_names = sorted(set(before) | set(after))
    changed_files = []
    runs = []
    for rel in all_names:
        b = before.get(rel, b"")
        a = after.get(rel, b"")
        if b == a:
            continue
        changed_files.append(rel)
        hint = any(x in rel.lower() for x in NAME_HINTS)
        for s, be, ae in _changed_runs(b, a):
            nearby = set(_nearby_ids(b, s, be, persons)) | set(_nearby_ids(a, s, ae, persons))
            runs.append(ChangedRun(
                rel, s, be, ae, max(0,be-s), max(0,ae-s),
                tuple(sorted(nearby)), hint
            ))
    return SnapshotDelta(
        label, str(before_package), str(after_package),
        int(changed_person_id) if changed_person_id is not None else None,
        changed_field, tuple(changed_files), tuple(runs)
    )


def load_manifest(path: str | Path):
    p = Path(path).expanduser()
    doc = json.loads(p.read_text(encoding="utf-8"))
    persons = {int(k): str(v) for k,v in doc.get("persons", {}).items()}
    snapshots = doc.get("snapshots", [])
    if not persons:
        raise ValueError("Manifest requires a persons mapping, e.g. {\"1\":\"Test Probe\"}.")
    if not snapshots:
        raise ValueError("Manifest requires at least one snapshot.")
    return doc, persons, snapshots


def analyse_manifest(path: str | Path):
    doc, persons, snapshots = load_manifest(path)
    baseline = Path(snapshots[0]["package"]).expanduser()
    hits, blobs = scan_person_ids(baseline, persons)
    candidates = find_index_candidates(blobs, persons)

    deltas = []
    for i in range(1, len(snapshots)):
        prev = snapshots[i-1]
        cur = snapshots[i]
        deltas.append(compare_packages(
            Path(prev["package"]).expanduser(),
            Path(cur["package"]).expanduser(),
            persons,
            label=cur.get("label", f"snapshot-{i}"),
            changed_person_id=cur.get("changed_person_id"),
            changed_field=cur.get("changed_field"),
        ))

    # Change-log candidate ranking: files changed in multiple deltas, especially
    # filenames with hints and runs near the declared changed person.
    file_stats = defaultdict(lambda: {"deltas":0, "hint":False, "person_matches":0})
    for d in deltas:
        seen = set()
        for run in d.runs:
            if run.file not in seen:
                file_stats[run.file]["deltas"] += 1
                seen.add(run.file)
            file_stats[run.file]["hint"] |= run.name_hint
            if d.changed_person_id is not None and d.changed_person_id in run.nearby_person_ids:
                file_stats[run.file]["person_matches"] += 1

    ranked = sorted(
        file_stats,
        key=lambda f: (
            -(file_stats[f]["deltas"] + 2*int(file_stats[f]["hint"]) + file_stats[f]["person_matches"]),
            f
        )
    )
    change_log_candidates = tuple(ranked[:20])

    # Verdict.
    strong_index = any(c.score >= .80 and len(c.matched_ids) >= min(3, len(persons)) for c in candidates)
    targeted_nav = any(
        d.changed_person_id is not None and
        any(d.changed_person_id in r.nearby_person_ids for r in d.runs)
        for d in deltas
    )
    hinted_log = any(any(x in f.lower() for x in ("change","log","history","journal")) for f in change_log_candidates)

    if strong_index and targeted_nav:
        verdict = "GO"
        reason = "Known Person IDs participate in a strong index candidate and controlled edits preserve person-linked navigation evidence."
    elif strong_index or targeted_nav or hinted_log:
        verdict = "PARTIAL"
        reason = "Navigation/index evidence exists, but the Person-ID-to-record path is not yet fully demonstrated."
    else:
        verdict = "INCONCLUSIVE"
        reason = "No strong Person Index or navigation reference has yet been isolated from the supplied snapshots."

    return NavigationSnapshot(
        hits=hits,
        index_candidates=candidates,
        deltas=tuple(deltas),
        candidate_change_log_files=change_log_candidates,
        package_files_scanned=len(blobs),
        verdict=verdict,
        verdict_reason=reason,
    )


def navigation_document(s: NavigationSnapshot):
    return {
        "schema":"reunion-companion.person-navigation-archaeology.v1",
        "phase":"Phase 4 - Navigation Archaeology",
        "build":23,
        "read_only":True,
        "summary":{
            "package_files_scanned":s.package_files_scanned,
            "person_id_hits":len(s.hits),
            "index_candidates":len(s.index_candidates),
            "snapshot_deltas":len(s.deltas),
            "candidate_change_log_files":len(s.candidate_change_log_files),
            "verdict":s.verdict,
            "verdict_reason":s.verdict_reason,
        },
        "index_candidates":[{
            "file":c.file,"encoding":c.encoding,"stride":c.stride,
            "start_offset":c.start_offset,"matched_ids":list(c.matched_ids),
            "score":c.score,"evidence":list(c.evidence)
        } for c in s.index_candidates[:500]],
        "hits":[{
            "person_id":h.person_id,"person_name":h.person_name,"file":h.file,
            "offset":h.offset,"encoding":h.encoding,"width":h.width,
            "context_hex":h.context_hex
        } for h in s.hits[:20000]],
        "deltas":[{
            "label":d.label,"before":d.before,"after":d.after,
            "changed_person_id":d.changed_person_id,"changed_field":d.changed_field,
            "changed_files":list(d.changed_files),
            "runs":[{
                "file":r.file,"start":r.start,"before_end":r.before_end,"after_end":r.after_end,
                "before_len":r.before_len,"after_len":r.after_len,
                "nearby_person_ids":list(r.nearby_person_ids),"name_hint":r.name_hint
            } for r in d.runs]
        } for d in s.deltas],
        "candidate_change_log_files":list(s.candidate_change_log_files),
    }


def write_stage23(manifest_path: str | Path, pipeline_dir: str | Path):
    s = analyse_manifest(manifest_path)
    a = make_artifact(23, "person-navigation-archaeology", navigation_document(s), {
        "manifest": str(Path(manifest_path).expanduser())
    })
    target = Path(pipeline_dir).expanduser() / "stage-23-person-navigation-archaeology.json"
    return write_artifact(target, a), s


def manifest_template():
    return {
      "schema":"reunion-companion.navigation-probe.v1",
      "persons":{
        "1":"Test Probe",
        "2":"Mary Probe",
        "3":"Baby Probe"
      },
      "snapshots":[
        {
          "label":"baseline",
          "package":"/path/Probe-00-Baseline.familyfile14"
        },
        {
          "label":"person1-birth-date",
          "package":"/path/Probe-01-P1-Birth-Date.familyfile14",
          "changed_person_id":1,
          "changed_field":"Birth Date"
        },
        {
          "label":"person2-birth-place",
          "package":"/path/Probe-02-P2-Birth-Place.familyfile14",
          "changed_person_id":2,
          "changed_field":"Birth Place"
        },
        {
          "label":"person1-research-note",
          "package":"/path/Probe-03-P1-Research-Note.familyfile14",
          "changed_person_id":1,
          "changed_field":"Research Note"
        }
      ]
    }
