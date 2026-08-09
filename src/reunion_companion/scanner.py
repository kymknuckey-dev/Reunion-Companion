"""Read-only package scanning primitives for Reunion Discovery Lab."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True, slots=True)
class PackageEntry:
    """One file or directory discovered inside a Reunion package."""

    relative_path: str
    size: int
    is_directory: bool

    @property
    def suffix(self) -> str:
        return Path(self.relative_path).suffix.casefold()


@dataclass(frozen=True, slots=True)
class PackageScan:
    """Structural inventory of a Reunion package."""

    package_path: str
    entries: tuple[PackageEntry, ...]
    total_bytes: int

    @property
    def file_count(self) -> int:
        return sum(1 for item in self.entries if not item.is_directory)

    @property
    def directory_count(self) -> int:
        return sum(1 for item in self.entries if item.is_directory)

    def files(self) -> list[PackageEntry]:
        return [item for item in self.entries if not item.is_directory]

    def by_suffix(self, suffix: str) -> list[PackageEntry]:
        needle = suffix.casefold()
        if needle and not needle.startswith("."):
            needle = "." + needle
        return [item for item in self.files() if item.suffix == needle]


class PackageScanner:
    """Inventory a Reunion package without interpreting or modifying it."""

    def scan(self, package_path: str | Path) -> PackageScan:
        root = Path(package_path).expanduser()
        if not root.exists():
            raise FileNotFoundError(root)

        entries: list[PackageEntry] = []

        if root.is_file():
            stat = root.stat()
            entries.append(
                PackageEntry(
                    relative_path=root.name,
                    size=stat.st_size,
                    is_directory=False,
                )
            )
        else:
            for path in sorted(root.rglob("*"), key=lambda p: str(p).casefold()):
                rel = path.relative_to(root).as_posix()
                if path.is_dir():
                    entries.append(
                        PackageEntry(
                            relative_path=rel,
                            size=0,
                            is_directory=True,
                        )
                    )
                else:
                    entries.append(
                        PackageEntry(
                            relative_path=rel,
                            size=path.stat().st_size,
                            is_directory=False,
                        )
                    )

        total = sum(item.size for item in entries if not item.is_directory)
        return PackageScan(
            package_path=str(root),
            entries=tuple(entries),
            total_bytes=total,
        )
