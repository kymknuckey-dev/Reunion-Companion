from pathlib import Path

from reunion_companion.discovery import PackageScanner, package_report


def test_package_report_markdown(tmp_path: Path) -> None:
    package = tmp_path / "Probe.familyfile14"
    package.mkdir()
    (package / "data").write_bytes(b"abc")

    scan = PackageScanner().scan(package)
    markdown = package_report(scan).to_markdown()

    assert "# Reunion Package Discovery Report" in markdown
    assert "Files: 1" in markdown
    assert "`data`" in markdown
