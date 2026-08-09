from __future__ import annotations
import json, shlex
from .architecture_reconstruction import (
    architecture_document, build_pipeline_artifacts, reconstruct_architecture
)
from .architecture_report import (
    architecture_markdown, format_architecture_components,
    format_architecture_probe, format_architecture_summary
)

HELP = [
    "  pipeline-build FILE Build Stage 16/17 versioned knowledge artifacts",
    "  architecture-summary FILE Show reconstructed architecture summary",
    "  architecture-components FILE Show architecture components",
    "  architecture-probe ID FILE Show evidence for one probe",
    "  architecture-report FILE Write architecture report/snapshot and pipeline artifacts",
]

def handle_build17_command(console, raw_command, command, default_report_path):
    if command.startswith("architecture-report "):
        parts = shlex.split(raw_command)
        if len(parts) != 2:
            return 'Usage: architecture-report "/path/PROBE_CORPUS_KNUCKEY.json"'
        snapshot, corpus = reconstruct_architecture(parts[1])
        target = default_report_path(console.package_path, "database_architecture")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(architecture_markdown(snapshot, corpus), encoding="utf-8")
        js = target.with_name("architecture_snapshot.json")
        js.write_text(json.dumps(architecture_document(snapshot, corpus), indent=2, sort_keys=True), encoding="utf-8")
        p16, p17 = build_pipeline_artifacts(parts[1], target.parent / "pipeline")
        return (
            f"Architecture report written: {target}\n"
            f"Architecture snapshot written: {js}\n"
            f"Pipeline artifacts written: {p16}, {p17}"
        )

    if command.startswith("architecture-probe "):
        parts = shlex.split(raw_command)
        if len(parts) != 3:
            return 'Usage: architecture-probe PROBE_ID "/path/PROBE_CORPUS_KNUCKEY.json"'
        snapshot, _ = reconstruct_architecture(parts[2])
        return format_architecture_probe(snapshot, parts[1])

    if command.startswith("architecture-components "):
        parts = shlex.split(raw_command)
        if len(parts) != 2:
            return 'Usage: architecture-components "/path/PROBE_CORPUS_KNUCKEY.json"'
        snapshot, _ = reconstruct_architecture(parts[1])
        return format_architecture_components(snapshot)

    if command.startswith("architecture-summary "):
        parts = shlex.split(raw_command)
        if len(parts) != 2:
            return 'Usage: architecture-summary "/path/PROBE_CORPUS_KNUCKEY.json"'
        snapshot, corpus = reconstruct_architecture(parts[1])
        return format_architecture_summary(snapshot, corpus)

    if command.startswith("pipeline-build "):
        parts = shlex.split(raw_command)
        if len(parts) != 2:
            return 'Usage: pipeline-build "/path/PROBE_CORPUS_KNUCKEY.json"'
        target = default_report_path(console.package_path, "database_architecture")
        p16, p17 = build_pipeline_artifacts(parts[1], target.parent / "pipeline")
        return f"Pipeline Stage 16 artifact: {p16}\nPipeline Stage 17 artifact: {p17}"

    return None
