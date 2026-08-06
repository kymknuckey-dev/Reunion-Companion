from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .domain import GenealogyTree, PersonProfile, load_genealogy_tree


def _event_markdown(event) -> list[str]:
    lines: list[str] = []
    heading = event.event_type.title()
    lines.append(f"### {heading}")
    lines.append("")

    if event.date and event.date.display:
        lines.append(f"**Date:** {event.date.display}")
    if event.place:
        lines.append(f"**Place:** {event.place}")
    if event.memo:
        lines.append("")
        lines.append(event.memo)

    if event.citations:
        lines.append("")
        lines.append("**Sources**")
        lines.append("")
        for citation in event.citations:
            title = citation.source_title or f"Source {citation.source_id}"
            lines.append(f"- **{title}**")
            if citation.detail:
                lines.append(f"  - {citation.detail}")

    lines.append("")
    return lines


def build_person_profile_markdown(
    tree: GenealogyTree,
    person: PersonProfile,
) -> str:
    lines: list[str] = [
        f"# {person.display}",
        "",
        f"**Person ID:** {person.id}",
        f"**Sex:** {person.sex or 'Unknown'}",
        "",
    ]

    lines.extend(["## Family", ""])

    if person.parent_ids:
        lines.append(
            "**Parents:** "
            + ", ".join(tree.person_name(person_id) for person_id in person.parent_ids)
        )
    else:
        lines.append("**Parents:** None decoded")

    if person.spouse_ids:
        lines.append(
            "**Spouses:** "
            + ", ".join(tree.person_name(person_id) for person_id in person.spouse_ids)
        )
    else:
        lines.append("**Spouses:** None decoded")

    if person.child_ids:
        lines.append(
            "**Children:** "
            + ", ".join(tree.person_name(person_id) for person_id in person.child_ids)
        )
    else:
        lines.append("**Children:** None decoded")

    lines.append("")

    if person.events:
        lines.extend(["## Events", ""])
        for event in person.events:
            lines.extend(_event_markdown(event))

    if person.notes:
        lines.extend(["## Notes", ""])
        for note in person.notes:
            lines.append(note.text)
            lines.append("")

    if person.media:
        lines.extend(["## Media", ""])
        for item in person.media:
            lines.append(f"### {item.filename or item.media_key}")
            lines.append("")
            lines.append(f"**Type:** {item.media_type or 'Unknown'}")
            if item.description:
                lines.append(f"**Description:** {item.description}")
            if item.caption:
                lines.append(f"**Comment:** {item.caption}")
            if item.original_path:
                lines.append(f"**Original path:** `{item.original_path}`")
            if item.thumbnails:
                sizes = ", ".join(str(thumb.size_hint) for thumb in item.thumbnails)
                lines.append(f"**Thumbnail sizes:** {sizes}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_person_profile_data(
    tree: GenealogyTree,
    person: PersonProfile,
) -> dict[str, object]:
    return {
        "person": asdict(person),
        "resolved_names": {
            "parents": [tree.person_name(item) for item in person.parent_ids],
            "spouses": [tree.person_name(item) for item in person.spouse_ids],
            "children": [tree.person_name(item) for item in person.child_ids],
        },
    }


def write_person_profile(
    package_path: str | Path,
    person_id: int,
    output_path: str | Path,
) -> Path:
    tree = load_genealogy_tree(package_path)
    person = tree.get_person(person_id)
    output = Path(output_path).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        build_person_profile_markdown(tree, person),
        encoding="utf-8",
    )
    return output.resolve()
