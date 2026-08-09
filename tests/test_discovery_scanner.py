from pathlib import Path

from reunion_companion.discovery import PackageScanner


def test_scanner_inventory_directory(tmp_path: Path) -> None:
    package = tmp_path / "Probe.familyfile14"
    package.mkdir()
    (package / "people.dat").write_bytes(b"abc")
    cache = package / "Caches"
    cache.mkdir()
    (cache / "names.cache").write_bytes(b"12345")

    scan = PackageScanner().scan(package)

    assert scan.file_count == 2
    assert scan.directory_count == 1
    assert scan.total_bytes == 8
    assert [item.relative_path for item in scan.files()] == [
        "Caches/names.cache",
        "people.dat",
    ]


def test_scanner_single_file(tmp_path: Path) -> None:
    package = tmp_path / "single.familyfile14"
    package.write_bytes(b"abcd")

    scan = PackageScanner().scan(package)

    assert scan.file_count == 1
    assert scan.total_bytes == 4
    assert scan.files()[0].relative_path == "single.familyfile14"
