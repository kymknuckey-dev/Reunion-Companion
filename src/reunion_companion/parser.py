from __future__ import annotations

from pathlib import Path

from .models import ReunionPackage


class ReunionFormatError(RuntimeError):
    """Raised when a supplied path is not a supported Reunion package."""


class BinaryReader:
    """Read-only access to a Reunion package and its main data file."""

    MAIN_FILES = {
        "14+": "familyfile.familydata",
        "10": "Family File.familyfile",
    }

    def __init__(self, package_path: str | Path) -> None:
        self.package_path = Path(package_path).expanduser().resolve()

    def inspect(self) -> ReunionPackage:
        if not self.package_path.exists():
            raise FileNotFoundError(self.package_path)
        if not self.package_path.is_dir():
            raise ReunionFormatError(
                f"Expected an unpacked Reunion package directory: {self.package_path}"
            )

        for version, filename in self.MAIN_FILES.items():
            candidate = self.package_path / filename
            if candidate.is_file():
                return ReunionPackage(
                    package_path=self.package_path,
                    version=version,
                    main_data_path=candidate,
                    main_data_size=candidate.stat().st_size,
                )

        raise ReunionFormatError(
            f"No recognised Reunion main data file found in {self.package_path}"
        )

    def read_main_data(self) -> bytes:
        package = self.inspect()
        return package.main_data_path.read_bytes()
