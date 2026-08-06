from __future__ import annotations

import argparse
import json
import sys

from .inventory import PackageInventory, build_inventory
from .parser import BinaryReader, ReunionFormatError
from .version import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reunion-companion",
        description="Read-only tools for Reunion genealogy family files.",
    )
    parser.add_argument("--version", action="version", version=__version__)

    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect a Reunion package without modifying it.",
    )
    inspect_parser.add_argument("package", help="Path to a .familyfile package directory")
    inspect_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON.",
    )

    inventory_parser = subparsers.add_parser(
        "inventory",
        help="Report package files and currently detectable Reunion structures.",
    )
    inventory_parser.add_argument("package", help="Path to a .familyfile package directory")
    inventory_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON.",
    )
    inventory_parser.add_argument(
        "--files",
        action="store_true",
        help="Include every package file in text output.",
    )
    inventory_parser.add_argument(
        "--people",
        action="store_true",
        help="List experimental person-name candidates in text output.",
    )

    return parser


def run_inspect(package_path: str, as_json: bool) -> int:
    package = BinaryReader(package_path).inspect()
    result = {
        "package_path": str(package.package_path),
        "version": package.version,
        "main_data_path": str(package.main_data_path),
        "main_data_size": package.main_data_size,
        "read_only": True,
    }

    if as_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Package:   {result['package_path']}")
        print(f"Version:   {result['version']}")
        print(f"Main file: {result['main_data_path']}")
        print(f"Size:      {result['main_data_size']:,} bytes")
        print("Mode:      read-only")

    return 0


def _print_inventory(inventory: PackageInventory, include_files: bool, include_people: bool) -> None:
    cache_files = [item for item in inventory.files if item.category == "cache"]

    print(f"Package:            {inventory.package_path}")
    print(f"Version:            {inventory.version}")
    print(f"Main data:          {inventory.main_data_size:,} bytes")
    print(f"Package files:      {inventory.total_files}")
    print(f"Package size:       {inventory.total_package_size:,} bytes")
    print(f"Cache files:        {len(cache_files)}")
    print()
    print("Currently detectable")
    print(f"  People candidates: {len(inventory.people)}")
    print(f"  Person tags:       {inventory.person_tags}")
    print(f"  Media strings:     {inventory.media_strings}")
    print(f"  Path strings:      {inventory.path_strings}")
    print(f"  Thumbnails:        {inventory.thumbnails.total}")
    print(f"    Person:          {inventory.thumbnails.person}")
    print(f"    Family:          {inventory.thumbnails.family}")
    print(f"    Unknown:         {inventory.thumbnails.unknown}")

    if include_people:
        print()
        print("Person candidates")
        if not inventory.people:
            print("  None detected")
        for person in inventory.people:
            print(f"  {person.display}  [offset {person.offset:,}]")

    if include_files:
        print()
        print("Package files")
        for item in inventory.files:
            print(f"  {item.relative_path:<48} {item.size:>10,}  {item.category}")

    print()
    print("Notes")
    for warning in inventory.warnings:
        print(f"  - {warning}")
    print("  - Read-only: no Reunion package files were changed.")


def run_inventory(package_path: str, as_json: bool, include_files: bool, include_people: bool) -> int:
    inventory = build_inventory(package_path)
    if as_json:
        print(json.dumps(inventory.to_dict(), indent=2))
    else:
        _print_inventory(inventory, include_files=include_files, include_people=include_people)
    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "inspect":
            raise SystemExit(run_inspect(args.package, args.json))
        if args.command == "inventory":
            raise SystemExit(
                run_inventory(
                    args.package,
                    args.json,
                    include_files=args.files,
                    include_people=args.people,
                )
            )
    except (FileNotFoundError, ReunionFormatError, PermissionError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
