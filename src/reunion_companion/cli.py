from __future__ import annotations

import argparse
import json
import sys

from .inventory import PackageInventory, build_inventory
from .parser import BinaryReader, ReunionFormatError
from .records import TreeExtraction, extract_tree
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
    inventory_parser.add_argument(
        "--cache-values",
        action="store_true",
        help="List decoded given names, surnames, places, and trailing index IDs.",
    )

    tree_parser = subparsers.add_parser(
        "tree",
        help="Extract structured people and a provisional family graph.",
    )
    tree_parser.add_argument("package", help="Path to a .familyfile package directory")
    tree_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON.",
    )
    tree_parser.add_argument(
        "--raw-fields",
        action="store_true",
        help="Include unresolved raw family-related values in text output.",
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


def _print_inventory(
    inventory: PackageInventory,
    include_files: bool,
    include_people: bool,
    include_cache_values: bool,
) -> None:
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

    print()
    print("Decoded caches")
    caches = inventory.caches
    print(f"  Given names:       {len(caches.given_names.values) if caches.given_names else 'unavailable'}")
    print(f"  Surnames:          {len(caches.surnames.values) if caches.surnames else 'unavailable'}")
    print(f"  Places:            {len(caches.places.values) if caches.places else 'unavailable'}")
    print(f"  Place usages:      {caches.place_usage_count if caches.place_usage_count is not None else 'unavailable'}")
    if caches.index:
        print(f"  Primary slots:     {caches.index.primary_slots}")
        print(f"  Family slots:      {caches.index.family_slots}")
    else:
        print("  Primary slots:     unavailable")
        print("  Family slots:      unavailable")

    if include_cache_values:
        print()
        print("Cache values")
        if caches.given_names:
            print("  Given names: " + ", ".join(caches.given_names.values))
        if caches.surnames:
            print("  Surnames:    " + ", ".join(caches.surnames.values))
        if caches.places:
            print("  Places:")
            for place in caches.places.values:
                print(f"    - {place}")
        if caches.index:
            ids = ", ".join(str(item) for item in caches.index.trailing_ids) or "none"
            print(f"  Trailing index IDs: {ids}")

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
    for warning in inventory.warnings + inventory.caches.warnings:
        print(f"  - {warning}")
    print("  - Read-only: no Reunion package files were changed.")


def run_inventory(
    package_path: str,
    as_json: bool,
    include_files: bool,
    include_people: bool,
    include_cache_values: bool,
) -> int:
    inventory = build_inventory(package_path)
    if as_json:
        print(json.dumps(inventory.to_dict(), indent=2))
    else:
        _print_inventory(
            inventory,
            include_files=include_files,
            include_people=include_people,
            include_cache_values=include_cache_values,
        )
    return 0



def _person_label(tree: TreeExtraction, person_id: int) -> str:
    person = next((item for item in tree.people if item.record_id == person_id), None)
    return person.display if person else f"Person {person_id}"


def run_tree(package_path: str, as_json: bool, include_raw_fields: bool) -> int:
    tree = extract_tree(package_path)
    if as_json:
        print(json.dumps(tree.to_dict(), indent=2))
        return 0

    print(f"Package: {tree.package_path}")
    print(f"Version: {tree.version}")
    print()
    print("Structured people")
    if not tree.people:
        print("  None decoded")
    for person in tree.people:
        sex = person.sex or f"unknown ({person.sex_code})"
        print(f"  Person {person.record_id}: {person.display}  [{sex}]")
        print(f"    Record offset: {person.offset:,}")
        if person.parent_family_ids:
            ids = ", ".join(str(item) for item in person.parent_family_ids)
            print(f"    Parent family: {ids}")
        if include_raw_fields and person.raw_family_values:
            values = ", ".join(str(item) for item in person.raw_family_values)
            print(f"    Raw 0x0064 values: {values}")

    print()
    print("Provisional families")
    if not tree.families:
        print("  None decoded")
    for family in tree.families:
        print(f"  Family {family.family_id}")
        if family.spouse_ids:
            spouses = " and ".join(
                _person_label(tree, person_id) for person_id in family.spouse_ids
            )
            print(f"    Spouses: {spouses}")
            print(f"    Spouse links: {family.spouse_link_status}")
        else:
            print("    Spouses: not yet decoded")
        if family.child_ids:
            children = ", ".join(
                _person_label(tree, person_id) for person_id in family.child_ids
            )
            print(f"    Children: {children}")
            print(f"    Child links: {family.child_link_status}")
        else:
            print("    Children: none decoded")

    print()
    print("Notes")
    for warning in tree.warnings:
        print(f"  - {warning}")
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
                    include_cache_values=args.cache_values,
                )
            )
        if args.command == "tree":
            raise SystemExit(
                run_tree(
                    args.package,
                    args.json,
                    include_raw_fields=args.raw_fields,
                )
            )
    except (FileNotFoundError, ReunionFormatError, PermissionError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
