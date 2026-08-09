from __future__ import annotations
import json, shlex
from .semantic_confidence import (
    build_confidence_from_pipeline,
    confidence_document,
    write_stage18_artifact,
)
from .semantic_confidence_report import (
    confidence_markdown,
    format_confidence_probe,
    format_confidence_region,
    format_confidence_summary,
)

HELP = [
    "  confidence-summary DIR Show Build 18 semantic-confidence summary",
    "  confidence-probe ID DIR Show confidence for one semantic probe",
    "  confidence-region CR-ID DIR Inspect one canonical-region confidence",
    "  confidence-build DIR Write persistent Stage 18 confidence artifact",
    "  confidence-report DIR Write semantic_confidence.md/json and Stage 18 artifact",
]

def handle_build18_command(console, raw_command, command, default_report_path):
    if command.startswith("confidence-report "):
        parts = shlex.split(raw_command)
        if len(parts) != 2:
            return 'Usage: confidence-report "/path/to/pipeline"'
        snapshot, *_ = build_confidence_from_pipeline(parts[1])
        target = default_report_path(console.package_path, "semantic_confidence")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(confidence_markdown(snapshot), encoding="utf-8")
        js = target.with_suffix(".json")
        js.write_text(
            json.dumps(confidence_document(snapshot), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        stage18, _ = write_stage18_artifact(parts[1])
        return (
            f"Semantic confidence report written: {target}\n"
            f"Semantic confidence JSON written: {js}\n"
            f"Pipeline Stage 18 artifact written: {stage18}"
        )

    if command.startswith("confidence-build "):
        parts = shlex.split(raw_command)
        if len(parts) != 2:
            return 'Usage: confidence-build "/path/to/pipeline"'
        stage18, snapshot = write_stage18_artifact(parts[1])
        return (
            f"Pipeline Stage 18 artifact: {stage18}\n"
            f"{format_confidence_summary(snapshot)}"
        )

    if command.startswith("confidence-region "):
        parts = shlex.split(raw_command)
        if len(parts) != 3:
            return 'Usage: confidence-region CR-ID "/path/to/pipeline"'
        snapshot, *_ = build_confidence_from_pipeline(parts[2])
        return format_confidence_region(snapshot, parts[1])

    if command.startswith("confidence-probe "):
        parts = shlex.split(raw_command)
        if len(parts) != 3:
            return 'Usage: confidence-probe PROBE_ID "/path/to/pipeline"'
        snapshot, *_ = build_confidence_from_pipeline(parts[2])
        return format_confidence_probe(snapshot, parts[1])

    if command.startswith("confidence-summary "):
        parts = shlex.split(raw_command)
        if len(parts) != 2:
            return 'Usage: confidence-summary "/path/to/pipeline"'
        snapshot, *_ = build_confidence_from_pipeline(parts[1])
        return format_confidence_summary(snapshot)

    return None
