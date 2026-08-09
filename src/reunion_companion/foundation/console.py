"""Interactive Foundation console.

Run:

    python -m reunion_companion.foundation.console "/path/to/file.familyfile14"
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

from .adapters import from_package
from .formatter import format_counts, format_person
from .diagnostics import FoundationDiagnostics
from .diagnostic_formatter import format_diagnostic_report, format_diagnostic_section
from .query import FoundationQueryEngine


BANNER = """\
========================================================
 Reunion Companion — Foundation Beta 1
========================================================
"""


def _extract_after(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip(" ?.") if match else None


def answer_question(engine: FoundationQueryEngine, question: str) -> str:
    """Route a small set of transparent natural-language queries."""
    raw = question.strip()
    lowered = raw.casefold()

    if not raw:
        return ""

    if lowered in {"help", "?"}:
        return HELP_TEXT

    if lowered in {"diagnostics", "diagnostic", "health"}:
        report = FoundationDiagnostics(engine.database).report()
        return format_diagnostic_report(report)

    diagnostic_sections = {
        "warnings": "Warnings",
        "event-types": "Events",
        "events-status": "Events",
        "source-coverage": "Sources",
        "sources-status": "Sources",
        "note-status": "Notes",
        "notes-status": "Notes",
        "media-status": "Media",
        "relationship-status": "Relationships",
    }
    if lowered in diagnostic_sections:
        report = FoundationDiagnostics(engine.database).report()
        return format_diagnostic_section(report.section(diagnostic_sections[lowered]))

    if lowered in {"stats", "summary", "counts"} or "how many" in lowered:
        counts = engine.summary()
        if "people" in lowered:
            return f"People: {counts['people']:,}"
        if "famil" in lowered:
            return f"Families: {counts['families']:,}"
        if "event" in lowered:
            return f"Events: {counts['events']:,}"
        if "place" in lowered:
            return f"Places: {counts['places']:,}"
        if "media" in lowered or "photo" in lowered:
            return f"Media: {counts['media']:,}"
        if "source" in lowered:
            return f"Sources: {counts['sources']:,}"
        if "note" in lowered:
            return f"Notes: {counts['notes']:,}"
        return "\n".join(f"{k.title()}: {v:,}" for k, v in counts.items())

    if "without" in lowered and "birth source" in lowered:
        people = engine.people_without_birth_source()
        return _format_people_list("People without a birth source", people)

    if ("photo" in lowered or "media" in lowered) and "without caption" in lowered:
        media = engine.photos_without_captions()
        if not media:
            return "No media without captions found."
        lines = [f"Media without captions ({len(media)}):"]
        lines.extend(f"  - {m.display_name} [{m.owner_type} {m.owner_id}]" for m in media[:200])
        if len(media) > 200:
            lines.append(f"  ... {len(media)-200} more")
        return "\n".join(lines)

    place = _extract_after(r"(?:people|events).*(?:in|at)\s+(.+)$", raw)
    if place and ("born" in lowered or "birth" in lowered):
        events = engine.events(event_type="birth", place=place)
        people = []
        seen = set()
        for event in events:
            if event.owner_type == "person" and event.owner_id not in seen:
                person = engine.database.people.find(event.owner_id)
                if person:
                    seen.add(person.id)
                    people.append(person)
        return _format_people_list(f"People born in {place}", people)

    if lowered.startswith("find person "):
        name = raw[len("find person "):].strip()
        return _person_lookup(engine, name)

    if lowered.startswith("tell me about "):
        name = raw[len("tell me about "):].strip(" .?")
        return _person_lookup(engine, name)

    if lowered.startswith("show person "):
        name = raw[len("show person "):].strip(" .?")
        return _person_lookup(engine, name)

    if lowered.startswith("find people "):
        text = raw[len("find people "):].strip(" .?")
        return _format_people_list(f"People matching {text}", engine.people(text))

    if lowered.startswith("find place "):
        text = raw[len("find place "):].strip(" .?")
        matches = engine.places(text)
        if not matches:
            return f"No places matched {text!r}."
        return "\n".join([f"Places matching {text!r} ({len(matches)}):"] +
                         [f"  - {p.name} [ID {p.id}]" for p in matches[:200]])

    if lowered.startswith("find source "):
        text = raw[len("find source "):].strip(" .?")
        matches = engine.sources(text)
        if not matches:
            return f"No sources matched {text!r}."
        return "\n".join([f"Sources matching {text!r} ({len(matches)}):"] +
                         [f"  - {s.title} [ID {s.id}]" for s in matches[:200]])

    if lowered.startswith("find media "):
        text = raw[len("find media "):].strip(" .?")
        matches = engine.media(text)
        if not matches:
            return f"No media matched {text!r}."
        return "\n".join([f"Media matching {text!r} ({len(matches)}):"] +
                         [f"  - {m.display_name} [{m.owner_type} {m.owner_id}]" for m in matches[:200]])

    return (
        "I don't yet have a deterministic Beta 1 query for that.\n"
        "Type 'help' to see the questions currently supported."
    )


def _person_lookup(engine: FoundationQueryEngine, name: str) -> str:
    person = engine.person(name)
    if person is not None:
        return format_person(person)

    matches = engine.people(name)
    if not matches:
        return f"No person matched {name!r}."
    return _format_people_list(f"Multiple people matched {name}", matches)


def _format_people_list(title: str, people) -> str:
    if not people:
        return f"{title}: none found."
    lines = [f"{title} ({len(people)}):"]
    lines.extend(f"  - {p.full_name} [ID {p.id}]" for p in people[:200])
    if len(people) > 200:
        lines.append(f"  ... {len(people)-200} more")
    return "\n".join(lines)


HELP_TEXT = """\
Supported Beta 1 questions/commands:

  stats
  how many people are in the database?
  tell me about Test Probe
  find person Mary Probe
  find people Probe
  find place Adelaide
  find source Certificate
  find media portrait
  show people without a birth source
  show photos without captions
  which people were born in Adelaide?

Diagnostics:
  diagnostics
  warnings
  event-types
  source-coverage
  note-status
  media-status
  relationship-status

Use 'quit' or 'exit' to leave.
"""


def load_database(package_path: str | Path):
    package_path = Path(package_path).expanduser()
    print(BANNER)
    print(f"Opening:\n{package_path}\n")
    print("Reading Reunion package and building Foundation database...")
    started = time.perf_counter()
    database = from_package(package_path)
    elapsed = time.perf_counter() - started
    print("✓ Foundation build successful\n")
    print(format_counts(database))
    print(f"\nBuild time    {elapsed:>8.2f} s")
    if database.warnings:
        print(f"Warnings      {len(database.warnings):>8,}")
    print()
    return database


def interactive(package_path: str | Path) -> int:
    database = load_database(package_path)
    engine = FoundationQueryEngine(database)

    print("Ready. Type 'help' for examples, or 'quit' to leave.\n")
    while True:
        try:
            question = input("Ask > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if question.casefold() in {"quit", "exit", "q"}:
            return 0

        answer = answer_question(engine, question)
        if answer:
            print(answer)
            print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="reunion-foundation",
        description="Interactive Foundation Beta 1 console",
    )
    parser.add_argument("package", help="Path to a Reunion .familyfile14 package")
    args = parser.parse_args(argv)

    try:
        return interactive(args.package)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
