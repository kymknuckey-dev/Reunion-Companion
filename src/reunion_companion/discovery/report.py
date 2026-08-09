"""Report generation for Reunion Discovery Lab."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .scanner import PackageScan


@dataclass(slots=True)
class DiscoveryReport:
    """Simple Markdown discovery report."""

    title: str
    sections: list[tuple[str, list[str]]] = field(default_factory=list)

    def add_section(self, title: str, lines: list[str]) -> None:
        self.sections.append((title, list(lines)))

    def to_markdown(self) -> str:
        output = [f"# {self.title}", ""]
        for title, lines in self.sections:
            output.extend([f"## {title}", ""])
            output.extend(lines or ["_No observations._"])
            output.append("")
        return "\n".join(output).rstrip() + "\n"

    def write(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.to_markdown(), encoding="utf-8")
        return target


def package_report(scan: PackageScan) -> DiscoveryReport:
    report = DiscoveryReport("Reunion Package Discovery Report")
    report.add_section(
        "Package",
        [
            f"- Path: `{scan.package_path}`",
            f"- Files: {scan.file_count:,}",
            f"- Directories: {scan.directory_count:,}",
            f"- Total bytes: {scan.total_bytes:,}",
        ],
    )
    report.add_section(
        "Files",
        [
            f"- `{entry.relative_path}` — {entry.size:,} bytes"
            for entry in scan.files()
        ],
    )
    return report


def default_report_path(
    package_path: str | Path,
    report_name: str,
    *,
    root: str | Path = "reports/discovery",
) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d")
    package = Path(package_path)
    package_name = package.name
    if package_name.endswith(".familyfile14"):
        package_name = package_name[:-len(".familyfile14")]
    package_name = package_name.replace(" ", "_")
    safe_name = report_name.replace(" ", "_")
    return Path(root) / package_name / stamp / f"{safe_name}.md"
