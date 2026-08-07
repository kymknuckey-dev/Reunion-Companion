from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import sys

from .inventory import PackageInventory, build_inventory
from .parser import BinaryReader, ReunionFormatError
from .records import TreeExtraction, extract_tree
from .domain import GenealogyTree, load_genealogy_tree, load_reunion_database
from .media import extract_media
from .sources import extract_sources
from .publishing import build_person_profile_data, build_person_profile_markdown, write_person_profile
from .query import ask_package
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

    person_parser = subparsers.add_parser(
        "person",
        help="Show a resolved person profile from the genealogy object model.",
    )
    person_parser.add_argument("package")
    selector = person_parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--id", type=int, dest="person_id")
    selector.add_argument("--name")
    person_parser.add_argument("--json", action="store_true")

    family_parser = subparsers.add_parser(
        "family",
        help="Show a resolved family unit from the genealogy object model.",
    )
    family_parser.add_argument("package")
    family_parser.add_argument("--id", type=int, required=True, dest="family_id")
    family_parser.add_argument("--json", action="store_true")

    media_parser = subparsers.add_parser(
        "media",
        help="List decoded Reunion media and thumbnail ownership.",
    )
    media_parser.add_argument("package")
    media_parser.add_argument("--json", action="store_true")

    sources_parser = subparsers.add_parser(
        "sources",
        help="List decoded master sources.",
    )
    sources_parser.add_argument("package")
    sources_parser.add_argument("--json", action="store_true")

    profile_parser = subparsers.add_parser(
        "profile",
        help="Generate a reusable person profile from the semantic model.",
    )
    profile_parser.add_argument("package")
    profile_parser.add_argument("--id", type=int, required=True, dest="person_id")
    profile_parser.add_argument(
        "--output",
        help="Write Markdown profile to this path instead of stdout.",
    )
    profile_parser.add_argument("--json", action="store_true")

    ask_parser = subparsers.add_parser(
        "ask",
        help="Ask a grounded question about decoded Reunion data.",
    )
    ask_parser.add_argument("package")
    ask_parser.add_argument("question")
    ask_parser.add_argument("--json", action="store_true")
    ask_parser.add_argument(
        "--evidence",
        action="store_true",
        help="Show the decoded evidence used for the answer.",
    )


    database_parser = subparsers.add_parser(
        "database",
        help="Show a semantic-model summary of the Reunion file.",
    )
    database_parser.add_argument("package")
    database_parser.add_argument("--json", action="store_true")

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
        for event in person.events:
            if event.date:
                print(f"    {event.event_type.title()}: {event.date.display}")
            if event.memo:
                print(f"      Memo: {event.memo}")
            if event.place:
                print(f"      Place: {event.place}")
        if include_raw_fields and person.raw_family_values:
            values = ", ".join(str(item) for item in person.raw_family_values)
            print(f"    Raw 0x0064 values: {values}")

    print()
    print("Structured families")
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
        for event in family.events:
            if event.date:
                print(f"    {event.event_type.title()}: {event.date.display}")
            if event.memo:
                print(f"      Memo: {event.memo}")
            if event.place:
                print(f"      Place: {event.place}")

    print()
    print("Notes")
    for warning in tree.warnings:
        print(f"  - {warning}")
    return 0


def _print_events(events) -> None:
    if not events:
        print("  Events: none decoded")
        return
    print("  Events")
    for event in events:
        line = f"    {event.event_type.title()}"
        if event.date and event.date.display:
            line += f": {event.date.display}"
        print(line)
        if event.place:
            print(f"      Place: {event.place}")
        if event.memo:
            print(f"      Memo: {event.memo}")
        for citation in event.citations:
            print("      Source")
            print(
                f"        {citation.source_title or f'Source {citation.source_id}'}"
            )
            if citation.detail:
                print(f"        Detail: {citation.detail}")


def _print_person_profile(tree: GenealogyTree, person) -> None:
    print(f"Person {person.id}: {person.display}")
    print(f"  Sex: {person.sex or 'unknown'}")
    print("  Parents: " + (
        ", ".join(tree.person_name(item) for item in person.parent_ids)
        if person.parent_ids else "none decoded"
    ))
    print("  Spouses: " + (
        ", ".join(tree.person_name(item) for item in person.spouse_ids)
        if person.spouse_ids else "none decoded"
    ))
    print("  Children: " + (
        ", ".join(tree.person_name(item) for item in person.child_ids)
        if person.child_ids else "none decoded"
    ))
    _print_events(person.events)
    if person.notes:
        print("  Notes")
        for note in person.notes:
            for line in note.text.splitlines() or [""]:
                print(f"    {line}")
    if person.media:
        print("  Media")
        for item in person.media:
            print(f"    {item.filename or item.media_key}")
            print(f"      Type: {item.media_type or 'unknown'}")
            print(f"      Fingerprint: {item.fingerprint}")
            print(f"      Thumbnails: {', '.join(str(t.size_hint) for t in item.thumbnails)}")
            if item.description:
                print(f"      Description: {item.description}")
            if item.caption:
                print(f"      Comment: {item.caption}")
            if item.original_path:
                print(f"      Original path: {item.original_path}")
    if person.notes:
        print("  Notes")
        for note in person.notes:
            for line in note.text.splitlines() or [""]:
                print(f"    {line}")
    else:
        print("  Notes: none decoded")


def run_person(package_path: str, person_id: int | None, name: str | None, as_json: bool) -> int:
    tree = load_genealogy_tree(package_path)
    people = [tree.get_person(person_id)] if person_id is not None else tree.find_people(name or "")
    if not people:
        print("No matching people found.", file=sys.stderr)
        return 1
    if as_json:
        payload = {
            "matches": [asdict(person) for person in people],
            "resolved_names": {
                str(person.id): {
                    "parents": [tree.person_name(item) for item in person.parent_ids],
                    "spouses": [tree.person_name(item) for item in person.spouse_ids],
                    "children": [tree.person_name(item) for item in person.child_ids],
                }
                for person in people
            },
        }
        print(json.dumps(payload, indent=2))
        return 0
    for index, person in enumerate(people):
        if index:
            print()
        _print_person_profile(tree, person)
    return 0


def run_family(package_path: str, family_id: int, as_json: bool) -> int:
    tree = load_genealogy_tree(package_path)
    family = tree.get_family(family_id)
    if as_json:
        payload = {
            "family": asdict(family),
            "spouse_names": [tree.person_name(item) for item in family.spouse_ids],
            "child_names": [tree.person_name(item) for item in family.child_ids],
        }
        print(json.dumps(payload, indent=2))
        return 0
    print(f"Family {family.id}")
    print("  Spouses: " + (
        " and ".join(tree.person_name(item) for item in family.spouse_ids)
        if family.spouse_ids else "none decoded"
    ))
    print("  Children: " + (
        ", ".join(tree.person_name(item) for item in family.child_ids)
        if family.child_ids else "none decoded"
    ))
    _print_events(family.events)
    return 0



def run_media(package_path: str, as_json: bool) -> int:
    items = extract_media(package_path)
    if as_json:
        print(json.dumps([item.to_dict() for item in items], indent=2))
        return 0
    if not items:
        print("No decoded media found.")
        return 0
    tree = load_genealogy_tree(package_path)
    print("Media")
    for item in items:
        print()
        print(f"  {item.filename or item.media_key}")
        print(f"    Owner: {item.owner_type.title()} {item.owner_id}")
        if item.owner_type == "person":
            print(f"    Person: {tree.person_name(item.owner_id)}")
        print(f"    Type: {item.media_type or 'unknown'}")
        print(f"    Fingerprint: {item.fingerprint}")
        print(f"    Filename link: {item.filename_link_status}")
        if item.description:
            print(f"    Description: {item.description}")
        if item.caption:
            print(f"    Comment: {item.caption}")
        if item.description or item.caption:
            print(f"    Metadata link: {item.metadata_link_status}")
        if item.original_path:
            print(f"    Original path: {item.original_path}")
        print("    Thumbnails")
        for thumb in item.thumbnails:
            print(
                f"      {thumb.size_hint}: {thumb.relative_path} "
                f"({thumb.byte_size:,} bytes)"
            )
    return 0



def run_sources(package_path: str, as_json: bool) -> int:
    sources = extract_sources(package_path)
    if as_json:
        print(json.dumps([asdict(source) for source in sources], indent=2))
        return 0
    if not sources:
        print("No decoded sources found.")
        return 0
    print("Sources")
    for source in sources:
        print()
        print(f"  Source {source.source_id}")
        print(f"    Title: {source.title}")
        print(f"    Type: {source.source_type}")
    return 0



def run_profile(
    package_path: str,
    person_id: int,
    output: str | None,
    as_json: bool,
) -> int:
    tree = load_genealogy_tree(package_path)
    person = tree.get_person(person_id)

    if as_json:
        print(json.dumps(build_person_profile_data(tree, person), indent=2))
        return 0

    if output:
        path = write_person_profile(package_path, person_id, output)
        print(f"Profile written: {path}")
        return 0

    print(build_person_profile_markdown(tree, person), end="")
    return 0



def run_ask(package_path: str, question: str, as_json: bool, show_evidence: bool) -> int:
    result = ask_package(package_path, question)
    if as_json:
        print(json.dumps(result.to_dict(), indent=2))
        return 0

    print(result.answer)
    if show_evidence and result.evidence:
        print()
        print("Evidence")
        for item in result.evidence:
            parts = [item.kind]
            if item.person_name:
                parts.append(item.person_name)
            if item.event_type:
                parts.append(item.event_type.title())
            if item.field:
                parts.append(item.field)
            if item.value:
                parts.append(item.value)
            if item.source_title:
                parts.append(item.source_title)
            if item.citation_detail:
                parts.append(item.citation_detail)
            print("  - " + " | ".join(parts))
    if result.limitations:
        print()
        print("Limits")
        for limitation in result.limitations:
            print(f"  - {limitation}")
    return 0 if result.intent != "unknown" else 1



def run_database(package_path: str, as_json: bool) -> int:
    database = load_reunion_database(package_path)
    summary = database.summary()

    if as_json:
        print(json.dumps({
            "package_path": database.package_path,
            "version": database.version,
            "summary": summary,
            "warnings": database.warnings,
        }, indent=2))
        return 0

    print(f"Database: {database.package_path}")
    print(f"Reunion version: {database.version}")
    print()
    print("Semantic model")
    labels = (
        ("People", "people"),
        ("Families", "families"),
        ("Person events", "person_events"),
        ("Family events", "family_events"),
        ("Places", "places"),
        ("Sources", "sources"),
        ("Citations", "citations"),
        ("Notes", "notes"),
        ("Media", "media"),
    )
    for label, key in labels:
        print(f"  {label:<16} {summary[key]:>6}")
    print()
    print("Mode: read-only")
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
        if args.command == "person":
            raise SystemExit(run_person(args.package, args.person_id, args.name, args.json))
        if args.command == "family":
            raise SystemExit(run_family(args.package, args.family_id, args.json))
        if args.command == "media":
            raise SystemExit(run_media(args.package, args.json))
        if args.command == "sources":
            raise SystemExit(run_sources(args.package, args.json))
        if args.command == "profile":
            raise SystemExit(
                run_profile(
                    args.package,
                    args.person_id,
                    args.output,
                    args.json,
                )
            )
        if args.command == "database":
            raise SystemExit(run_database(args.package, args.json))
        if args.command == "ask":
            raise SystemExit(
                run_ask(args.package, args.question, args.json, args.evidence)
            )
    except (FileNotFoundError, ReunionFormatError, PermissionError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
