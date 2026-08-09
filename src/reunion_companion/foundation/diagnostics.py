"""Diagnostics for understanding real Reunion databases.

Beta 2 deliberately reports what is present, linked, unresolved, or absent.
It does not guess at missing Reunion data.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .database import FoundationDatabase


@dataclass(slots=True)
class DiagnosticSection:
    """Named block of diagnostic metrics."""

    title: str
    metrics: dict[str, int | float | str] = field(default_factory=dict)
    details: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DiagnosticReport:
    """Complete Foundation database diagnostic report."""

    sections: list[DiagnosticSection]

    def section(self, title: str) -> DiagnosticSection:
        for section in self.sections:
            if section.title.casefold() == title.casefold():
                return section
        raise KeyError(title)

    def to_dict(self) -> dict[str, dict[str, int | float | str | list[str]]]:
        return {
            section.title: {
                **section.metrics,
                "details": list(section.details),
            }
            for section in self.sections
        }


class FoundationDiagnostics:
    """Inspect Foundation data quality and coverage."""

    def __init__(self, database: FoundationDatabase) -> None:
        self.database = database

    def report(self) -> DiagnosticReport:
        return DiagnosticReport(
            sections=[
                self.package_section(),
                self.object_section(),
                self.relationship_section(),
                self.event_section(),
                self.source_section(),
                self.note_section(),
                self.media_section(),
                self.warning_section(),
            ]
        )

    def package_section(self) -> DiagnosticSection:
        return DiagnosticSection(
            "Package",
            {
                "version": self.database.version or "unknown",
                "package_path": self.database.package_path or "",
            },
        )

    def object_section(self) -> DiagnosticSection:
        return DiagnosticSection("Objects", dict(self.database.object_counts))

    def relationship_section(self) -> DiagnosticSection:
        people = list(self.database.people)

        with_parents = sum(1 for person in people if person.parents)
        with_spouses = sum(1 for person in people if person.spouses)
        with_children = sum(1 for person in people if person.children)

        parent_links = sum(len(person.parents) for person in people)
        spouse_links = sum(len(person.spouses) for person in people)
        child_links = sum(len(person.children) for person in people)

        return DiagnosticSection(
            "Relationships",
            {
                "people_with_parents": with_parents,
                "people_with_spouses": with_spouses,
                "people_with_children": with_children,
                "parent_links": parent_links,
                "spouse_links": spouse_links,
                "child_links": child_links,
            },
        )

    def event_section(self) -> DiagnosticSection:
        events = list(self.database.events)
        by_type = Counter(
            (event.event_type or "(blank)").strip() or "(blank)"
            for event in events
        )
        with_dates = sum(1 for event in events if event.has_date)
        with_places = sum(1 for event in events if event.has_place)
        with_memos = sum(1 for event in events if (event.memo or "").strip())
        with_citations = sum(1 for event in events if event.citations)
        unresolved_places = sum(
            1
            for event in events
            if event.place is None and bool((event.place_text or "").strip())
        )

        details = [
            f"{event_type}: {count}"
            for event_type, count in sorted(
                by_type.items(),
                key=lambda item: (-item[1], item[0].casefold()),
            )
        ]

        return DiagnosticSection(
            "Events",
            {
                "total": len(events),
                "types": len(by_type),
                "with_dates": with_dates,
                "with_places": with_places,
                "with_memos": with_memos,
                "with_citations": with_citations,
                "unresolved_place_text": unresolved_places,
            },
            details,
        )

    def source_section(self) -> DiagnosticSection:
        sources = list(self.database.sources)
        citations = list(self.database.citations)

        resolved = sum(1 for citation in citations if citation.resolved)
        unresolved = len(citations) - resolved
        used_sources = sum(1 for source in sources if source.citations)
        unused_sources = len(sources) - used_sources

        cited_people = sum(1 for person in self.database.people if person.citations)
        cited_families = sum(1 for family in self.database.families if family.citations)

        return DiagnosticSection(
            "Sources",
            {
                "sources": len(sources),
                "citations": len(citations),
                "resolved_citations": resolved,
                "unresolved_citations": unresolved,
                "used_sources": used_sources,
                "unused_sources": unused_sources,
                "people_with_citations": cited_people,
                "families_with_citations": cited_families,
            },
        )

    def note_section(self) -> DiagnosticSection:
        notes = list(self.database.notes)
        person_notes = sum(1 for note in notes if note.owner_type == "person")
        family_notes = sum(1 for note in notes if note.owner_type == "family")
        empty_notes = sum(1 for note in notes if note.is_empty)

        owners_with_notes = sum(1 for person in self.database.people if person.notes)
        family_owners_with_notes = sum(
            1 for family in self.database.families if family.notes
        )

        return DiagnosticSection(
            "Notes",
            {
                "notes": len(notes),
                "person_notes": person_notes,
                "family_notes": family_notes,
                "empty_notes": empty_notes,
                "people_with_notes": owners_with_notes,
                "families_with_notes": family_owners_with_notes,
            },
        )

    def media_section(self) -> DiagnosticSection:
        media = list(self.database.media)

        with_filename = sum(1 for item in media if (item.filename or "").strip())
        with_path = sum(1 for item in media if (item.original_path or "").strip())
        with_caption = sum(1 for item in media if (item.caption or "").strip())
        with_description = sum(
            1 for item in media if (item.description or "").strip()
        )
        with_metadata = sum(1 for item in media if item.has_metadata)

        person_media = sum(1 for item in media if item.owner_type == "person")
        family_media = sum(1 for item in media if item.owner_type == "family")

        unresolved_filename = sum(
            1
            for item in media
            if item.filename_link_status
            and "unresolved" in item.filename_link_status.casefold()
        )
        unresolved_metadata = sum(
            1
            for item in media
            if item.metadata_link_status
            and "unresolved" in item.metadata_link_status.casefold()
        )

        return DiagnosticSection(
            "Media",
            {
                "media": len(media),
                "person_media": person_media,
                "family_media": family_media,
                "with_filename": with_filename,
                "with_path": with_path,
                "with_caption": with_caption,
                "with_description": with_description,
                "with_metadata": with_metadata,
                "without_caption": len(media) - with_caption,
                "without_description": len(media) - with_description,
                "unresolved_filename_links": unresolved_filename,
                "unresolved_metadata_links": unresolved_metadata,
            },
        )

    def warning_section(self) -> DiagnosticSection:
        return DiagnosticSection(
            "Warnings",
            {"count": len(self.database.warnings)},
            list(self.database.warnings),
        )
