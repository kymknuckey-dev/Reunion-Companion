"""Build 15 Semantic Noise Suppression & Differential Alignment Engine."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
import json
import re

from .differential_verification import ByteSpanDelta, DifferentialResult, compare_packages_differential

NOISE_CATEGORIES = {"DOCUMENT_PATH", "UI_ARCHIVE", "CACHE_INDEX", "DERIVED_BINARY"}
SEMANTIC_CATEGORIES = {"DECODED_EVENT", "STRUCTURAL_SEMANTIC", "TEXT_SEMANTIC_CANDIDATE"}

_PATH_MARKERS = (
    "/Users/", "file:///", ".familyfile14", "familyfile.familydata", "Reunion Files",
)
_UI_MARKERS = (
    "NSMutableDictionary", "NSDictionary", "NSMutableArray", "NSArray",
    "NSString", "NSNumber", "NSValue", "NSObject", "LucidaGrande",
    "Recent Results", "flFrame", "font", "color", "tfField", "tfType",
    "tfTitle", "tfWrap", "pPict", "sExEmpty", "cExEmpty",
)
_CACHE_MARKERS = (".cache", "bookmarks", "timestamps", "recent", "window", "frame")
_SEMANTIC_MARKERS = ("[[pt:", "BD&M", "Certificate", "reference", "Test Probe", "Probe ")


@dataclass(frozen=True, slots=True)
class SpanAssessment:
    index: int
    category: str
    confidence: float
    suppressed: bool
    reason: str
    span: ByteSpanDelta


@dataclass(frozen=True, slots=True)
class SuppressedDifferential:
    result: DifferentialResult
    assessments: tuple[SpanAssessment, ...]
    semantic_spans: tuple[SpanAssessment, ...]
    noise_spans: tuple[SpanAssessment, ...]
    unknown_spans: tuple[SpanAssessment, ...]

    @property
    def suppression_ratio(self) -> float:
        return (len(self.noise_spans) / len(self.assessments)) if self.assessments else 0.0


@dataclass(frozen=True, slots=True)
class ProbeSpec:
    probe_id: str
    semantic_label: str
    operation: str
    before: str
    after: str


@dataclass(frozen=True, slots=True)
class CorpusPattern:
    signature: str
    category: str
    probes: tuple[str, ...]
    occurrences: int
    recurrence: float


@dataclass(frozen=True, slots=True)
class CorpusProbeResult:
    spec: ProbeSpec
    differential: SuppressedDifferential


@dataclass(frozen=True, slots=True)
class CorpusSummary:
    probes: int
    add_probes: int
    modify_probes: int
    compound_probes: int
    total_spans: int
    suppressed_noise_spans: int
    semantic_candidate_spans: int
    unknown_spans: int
    recurring_patterns: int


def _span_text(span: ByteSpanDelta) -> str:
    return f"{span.before_ascii}\n{span.after_ascii}"


def _printable_ratio(span: ByteSpanDelta) -> float:
    text = (span.before_ascii or "") + (span.after_ascii or "")
    if not text:
        return 0.0
    return sum(1 for ch in text if ch != ".") / len(text)


def _near_decoded_event(result: DifferentialResult, span: ByteSpanDelta, radius: int = 768) -> bool:
    for event in result.decoded_event_deltas:
        for offset in (event.before_record_offset, event.after_record_offset):
            if offset is None:
                continue
            if abs(span.before_start - offset) <= radius or abs(span.after_start - offset) <= radius:
                return True
    return False


def assess_span(result: DifferentialResult, span: ByteSpanDelta, *, index: int) -> SpanAssessment:
    text = _span_text(span)

    if _near_decoded_event(result, span):
        return SpanAssessment(index, "DECODED_EVENT", 0.99, False,
                              "span lies near a decoded changed event record", span)

    if any(marker in text for marker in _PATH_MARKERS):
        return SpanAssessment(index, "DOCUMENT_PATH", 0.99, True,
                              "contains document/package path metadata", span)

    ui_hits = sum(1 for marker in _UI_MARKERS if marker in text)
    if ui_hits:
        return SpanAssessment(index, "UI_ARCHIVE", min(0.99, 0.82 + 0.03 * ui_hits), True,
                              f"contains {ui_hits} Cocoa/UI archive marker(s)", span)

    cache_hits = sum(1 for marker in _CACHE_MARKERS if marker.casefold() in text.casefold())
    if cache_hits:
        return SpanAssessment(index, "CACHE_INDEX", min(0.96, 0.76 + 0.04 * cache_hits), True,
                              f"contains {cache_hits} cache/index marker(s)", span)

    semantic_hits = sum(1 for marker in _SEMANTIC_MARKERS if marker in text)
    if semantic_hits:
        return SpanAssessment(index, "TEXT_SEMANTIC_CANDIDATE",
                              min(0.98, 0.76 + 0.05 * semantic_hits), False,
                              f"contains {semantic_hits} genealogy/person token(s)", span)

    if result.structure_changed and max(span.before_length, span.after_length) <= 1024:
        return SpanAssessment(index, "STRUCTURAL_SEMANTIC", 0.72, False,
                              "Object Class/alignment structure changed in this probe", span)

    if max(span.before_length, span.after_length) >= 256 and _printable_ratio(span) < 0.08:
        return SpanAssessment(index, "DERIVED_BINARY", 0.70, True,
                              "large low-printable rewritten binary block", span)

    return SpanAssessment(index, "UNKNOWN", 0.35, False,
                          "not yet explained by decoded, structural, path, UI, cache or text evidence", span)


def suppress_noise(result: DifferentialResult) -> SuppressedDifferential:
    assessments = tuple(assess_span for assess_span in (
        assess_span(result, span, index=i)
        for i, span in enumerate(result.byte_spans, start=1)
    ))
    return SuppressedDifferential(
        result=result,
        assessments=assessments,
        semantic_spans=tuple(a for a in assessments if a.category in SEMANTIC_CATEGORIES),
        noise_spans=tuple(a for a in assessments if a.category in NOISE_CATEGORIES),
        unknown_spans=tuple(a for a in assessments if a.category == "UNKNOWN"),
    )


def _normalized_signature(assessment: SpanAssessment) -> str:
    text = _span_text(assessment.span)
    text = re.sub(r"/Users/[^\s]+", "<PATH>", text)
    text = re.sub(r"\d+", "#", text)
    tokens = [
        marker for marker in (_PATH_MARKERS + _UI_MARKERS + _CACHE_MARKERS + _SEMANTIC_MARKERS)
        if marker.casefold() in text.casefold()
    ]
    if tokens:
        return assessment.category + ":" + "|".join(sorted(set(tokens)))
    size = max(assessment.span.before_length, assessment.span.after_length)
    size_bucket = min(4096, ((size + 31) // 32) * 32)
    return f"{assessment.category}:size={size_bucket}:print={_printable_ratio(assessment.span):.1f}"


def recurring_patterns(results: Sequence[CorpusProbeResult], *, minimum_probes: int = 2) -> list[CorpusPattern]:
    probe_sets = defaultdict(set)
    counts = Counter()
    for item in results:
        local = set()
        for assessment in item.differential.assessments:
            key = (assessment.category, _normalized_signature(assessment))
            counts[key] += 1
            local.add(key)
        for key in local:
            probe_sets[key].add(item.spec.probe_id)

    population = len(results)
    patterns = []
    for (category, signature), probes in probe_sets.items():
        if len(probes) < minimum_probes:
            continue
        patterns.append(CorpusPattern(
            signature=signature,
            category=category,
            probes=tuple(sorted(probes)),
            occurrences=counts[(category, signature)],
            recurrence=(len(probes) / population) if population else 0.0,
        ))
    return sorted(patterns, key=lambda p: (-p.recurrence, -p.occurrences, p.category, p.signature))


def load_corpus_manifest(path: str | Path) -> list[ProbeSpec]:
    doc = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or not isinstance(doc.get("probes"), list):
        raise ValueError("Corpus manifest must contain a 'probes' list.")
    specs = []
    for i, row in enumerate(doc["probes"], start=1):
        probe_id = str(row.get("id") or f"probe-{i:03d}")
        label = str(row.get("semantic_label") or "").strip()
        operation = str(row.get("operation") or "MODIFY").strip().upper()
        before = str(row.get("before") or "")
        after = str(row.get("after") or "")
        if operation not in {"ADD", "MODIFY", "COMPOUND"}:
            raise ValueError(f"Probe {probe_id}: operation must be ADD, MODIFY or COMPOUND.")
        if not label or not before or not after:
            raise ValueError(f"Probe {probe_id}: semantic_label, before and after are required.")
        specs.append(ProbeSpec(probe_id, label, operation, before, after))
    return specs


def run_corpus_manifest(path: str | Path):
    specs = load_corpus_manifest(path)
    results = []
    for spec in specs:
        raw = compare_packages_differential(spec.before, spec.after, declared_change=spec.semantic_label)
        results.append(CorpusProbeResult(spec, suppress_noise(raw)))

    patterns = recurring_patterns(results)
    summary = CorpusSummary(
        probes=len(results),
        add_probes=sum(1 for x in results if x.spec.operation == "ADD"),
        modify_probes=sum(1 for x in results if x.spec.operation == "MODIFY"),
        compound_probes=sum(1 for x in results if x.spec.operation == "COMPOUND"),
        total_spans=sum(len(x.differential.assessments) for x in results),
        suppressed_noise_spans=sum(len(x.differential.noise_spans) for x in results),
        semantic_candidate_spans=sum(len(x.differential.semantic_spans) for x in results),
        unknown_spans=sum(len(x.differential.unknown_spans) for x in results),
        recurring_patterns=len(patterns),
    )
    return results, patterns, summary


def corpus_document(results, patterns, summary) -> dict:
    return {
        "schema": "reunion-companion.semantic-noise-corpus.v1",
        "phase": "Phase 2 - Semantic Discovery",
        "build": 15,
        "summary": {
            "probes": summary.probes,
            "add_probes": summary.add_probes,
            "modify_probes": summary.modify_probes,
            "compound_probes": summary.compound_probes,
            "total_spans": summary.total_spans,
            "suppressed_noise_spans": summary.suppressed_noise_spans,
            "semantic_candidate_spans": summary.semantic_candidate_spans,
            "unknown_spans": summary.unknown_spans,
            "recurring_patterns": summary.recurring_patterns,
        },
        "patterns": [
            {
                "signature": p.signature,
                "category": p.category,
                "probes": list(p.probes),
                "occurrences": p.occurrences,
                "recurrence": p.recurrence,
            } for p in patterns
        ],
        "probes": [
            {
                "id": item.spec.probe_id,
                "semantic_label": item.spec.semantic_label,
                "operation": item.spec.operation,
                "raw_changed": item.differential.result.raw_changed,
                "decoded_event_changes": len(item.differential.result.decoded_event_deltas),
                "class_changes": len(item.differential.result.class_deltas),
                "alignment_changes": len(item.differential.result.edge_deltas),
                "span_counts": {
                    "all": len(item.differential.assessments),
                    "semantic": len(item.differential.semantic_spans),
                    "noise": len(item.differential.noise_spans),
                    "unknown": len(item.differential.unknown_spans),
                },
            } for item in results
        ],
    }
