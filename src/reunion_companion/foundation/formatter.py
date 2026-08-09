"""Text formatting for the Foundation interactive console."""

from __future__ import annotations

from .database import FoundationDatabase
from .person import FoundationPerson


def format_counts(database: FoundationDatabase) -> str:
    counts = database.object_counts
    order = (
        "people",
        "families",
        "events",
        "places",
        "media",
        "notes",
        "sources",
        "citations",
    )
    return "\n".join(
        f"{name.title():<12}{counts.get(name, 0):>8,}"
        for name in order
    )


def format_person(person: FoundationPerson) -> str:
    lines = [person.full_name, "=" * len(person.full_name)]

    lines.append(f"ID: {person.id}")
    if person.sex and person.sex != "unknown":
        lines.append(f"Sex: {person.sex}")

    if person.parents:
        lines.append("Parents: " + ", ".join(p.full_name for p in person.parents))
    if person.spouses:
        lines.append("Spouses: " + ", ".join(p.full_name for p in person.spouses))
    if person.children:
        lines.append("Children: " + ", ".join(p.full_name for p in person.children))

    if person.events:
        lines.append("")
        lines.append("Events")
        for event in person.events:
            lines.append(f"  - {event}")

    if person.notes:
        lines.append("")
        lines.append(f"Notes: {len(person.notes)}")
        for note in person.notes[:3]:
            preview = " ".join(note.text.split())
            if len(preview) > 120:
                preview = preview[:117] + "..."
            lines.append(f"  - {preview}")

    if person.media:
        lines.append("")
        lines.append(f"Media: {len(person.media)}")
        for media in person.media[:10]:
            lines.append(f"  - {media.display_name}")

    if person.citations:
        lines.append("")
        lines.append(f"Citations: {len(person.citations)}")
        for citation in person.citations[:10]:
            detail = f" — {citation.detail}" if citation.detail else ""
            lines.append(f"  - {citation.display_source}{detail}")

    return "\n".join(lines)
