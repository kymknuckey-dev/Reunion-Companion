"""Formatting helpers for Foundation diagnostics."""

from __future__ import annotations

from .diagnostics import DiagnosticReport, DiagnosticSection


def format_diagnostic_section(section: DiagnosticSection) -> str:
    lines = [section.title, "-" * len(section.title)]
    if section.metrics:
        width = max(len(str(key)) for key in section.metrics)
        for key, value in section.metrics.items():
            label = key.replace("_", " ").title()
            if isinstance(value, int):
                rendered = f"{value:,}"
            elif isinstance(value, float):
                rendered = f"{value:.2f}"
            else:
                rendered = str(value)
            lines.append(f"{label:<{width + 4}} {rendered}")

    if section.details:
        if section.metrics:
            lines.append("")
        lines.extend(section.details)

    return "\n".join(lines)


def format_diagnostic_report(report: DiagnosticReport) -> str:
    return "\n\n".join(format_diagnostic_section(section) for section in report.sections)
