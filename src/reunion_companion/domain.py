from __future__ import annotations

from pathlib import Path

from .caches import decode_place_map
from .media import extract_media
from .model import (
    Family,
    GenealogyTree,
    Media,
    Person,
    Place,
    ReunionDatabase,
)
from .records import TreeExtraction, extract_tree
from .sources import extract_sources


# Backwards-compatible names from v0.2-v0.5.
PersonProfile = Person
FamilyUnit = Family


def build_reunion_database(extraction: TreeExtraction) -> ReunionDatabase:
    people = {
        item.record_id: Person(
            id=item.record_id,
            given=item.given,
            surname=item.surname,
            display=item.display,
            sex=item.sex,
            events=list(item.events),
            notes=list(item.notes),
            parent_family_ids=list(item.parent_family_ids),
            evidence={
                "identity": _evidence("decoded-controlled-probes"),
                "relationships": _evidence("decoded-controlled-probes"),
            },
        )
        for item in extraction.people
    }

    families = {
        item.family_id: Family(
            id=item.family_id,
            spouse_ids=list(item.spouse_ids),
            child_ids=list(item.child_ids),
            events=list(item.events),
            evidence={
                "spouses": _evidence(item.spouse_link_status),
                "children": _evidence(item.child_link_status),
            },
        )
        for item in extraction.families
    }

    for family in families.values():
        for spouse_id in family.spouse_ids:
            spouse = people.get(spouse_id)
            if spouse is None:
                continue
            spouse.spouse_ids.extend(
                candidate
                for candidate in family.spouse_ids
                if candidate != spouse_id and candidate not in spouse.spouse_ids
            )
            spouse.child_ids.extend(
                child_id
                for child_id in family.child_ids
                if child_id not in spouse.child_ids
            )

        for child_id in family.child_ids:
            child = people.get(child_id)
            if child is None:
                continue
            child.parent_ids.extend(
                parent_id
                for parent_id in family.spouse_ids
                if parent_id not in child.parent_ids
            )

    return ReunionDatabase(
        package_path=extraction.package_path,
        version=extraction.version,
        people=people,
        families=families,
        warnings=list(extraction.warnings),
    )


def _evidence(status: str):
    from .model import Evidence
    return Evidence(status=status)


def build_genealogy_tree(extraction: TreeExtraction) -> GenealogyTree:
    """Historical API retained as an alias of build_reunion_database."""
    return build_reunion_database(extraction)


def load_reunion_database(package_path: str | Path) -> ReunionDatabase:
    database = build_reunion_database(extract_tree(package_path))

    database.sources = {
        source.source_id: source
        for source in extract_sources(package_path)
    }

    for person in database.people.values():
        for event in person.events:
            for citation in event.citations:
                source = database.sources.get(citation.source_id)
                if source is not None:
                    citation.source_title = source.title

    for family in database.families.values():
        for event in family.events:
            for citation in event.citations:
                source = database.sources.get(citation.source_id)
                if source is not None:
                    citation.source_title = source.title

    for item in extract_media(package_path):
        database.media[item.media_key] = item
        if item.owner_type == "person":
            person = database.people.get(item.owner_id)
            if person is not None:
                person.media.append(item)
        elif item.owner_type == "family":
            family = database.families.get(item.owner_id)
            if family is not None:
                family.media.append(item)

    places_path = Path(database.package_path) / "places.cache"
    if places_path.is_file():
        try:
            database.places = {
                place_id: Place(id=place_id, name=name)
                for place_id, name in decode_place_map(places_path.read_bytes()).items()
            }
        except Exception:
            database.places = {}

    return database


def load_genealogy_tree(package_path: str | Path) -> GenealogyTree:
    """Historical API retained as an alias of load_reunion_database."""
    return load_reunion_database(package_path)


__all__ = [
    "FamilyUnit",
    "GenealogyTree",
    "PersonProfile",
    "ReunionDatabase",
    "build_genealogy_tree",
    "build_reunion_database",
    "load_genealogy_tree",
    "load_reunion_database",
]
