"""Build Foundation objects from the verified v0.9 semantic model."""

from __future__ import annotations

from dataclasses import dataclass

from reunion_companion.model import ReunionDatabase

from .citation import FoundationCitation
from .database import FoundationDatabase
from .event import FoundationEvent
from .family import FoundationFamily
from .media import FoundationMedia
from .note import FoundationNote
from .person import FoundationPerson
from .place import FoundationPlace
from .source import FoundationSource


@dataclass(slots=True)
class FoundationBuildReport:
    people: int
    families: int
    events: int
    places: int
    notes: int
    media: int
    sources: int
    citations: int
    warnings: int

    def to_dict(self) -> dict[str, int]:
        return {
            "people": self.people,
            "families": self.families,
            "events": self.events,
            "places": self.places,
            "notes": self.notes,
            "media": self.media,
            "sources": self.sources,
            "citations": self.citations,
            "warnings": self.warnings,
        }


class FoundationBuilder:
    """Convert an existing semantic Reunion database into Foundation objects."""

    def build(self, source: ReunionDatabase) -> FoundationDatabase:
        database = FoundationDatabase(
            package_path=source.package_path,
            version=source.version,
            warnings=list(source.warnings),
        )

        self._build_places(source, database)
        self._build_people(source, database)
        self._build_families(source, database)
        self._link_relationships(source, database)
        self._build_sources(source, database)
        self._build_notes(source, database)
        event_map = self._build_events(source, database)
        self._build_media(source, database)
        self._build_citations(source, database, event_map)
        database.rebuild_indexes()
        return database

    def build_with_report(
        self,
        source: ReunionDatabase,
    ) -> tuple[FoundationDatabase, FoundationBuildReport]:
        database = self.build(source)
        counts = database.object_counts
        return database, FoundationBuildReport(
            people=counts["people"],
            families=counts["families"],
            events=counts["events"],
            places=counts["places"],
            notes=counts["notes"],
            media=counts["media"],
            sources=counts["sources"],
            citations=counts["citations"],
            warnings=len(database.warnings),
        )

    @staticmethod
    def _build_places(source: ReunionDatabase, database: FoundationDatabase) -> None:
        for place_id, place in sorted(source.places.items()):
            database.add_place(
                FoundationPlace(
                    object_id=place_id,
                    name=place.name,
                    latitude=place.latitude,
                    longitude=place.longitude,
                    metadata={"semantic_model": "v0.9"},
                )
            )

    @staticmethod
    def _build_people(source: ReunionDatabase, database: FoundationDatabase) -> None:
        for person_id, person in sorted(source.people.items()):
            database.add_person(
                FoundationPerson(
                    object_id=person_id,
                    given=person.given,
                    surname=person.surname,
                    display_name=person.display,
                    sex=person.sex or "unknown",
                    metadata={
                        "semantic_model": "v0.9",
                        "parent_family_ids": list(person.parent_family_ids),
                    },
                )
            )

    @staticmethod
    def _build_families(source: ReunionDatabase, database: FoundationDatabase) -> None:
        for family_id in sorted(source.families):
            database.add_family(
                FoundationFamily(
                    object_id=family_id,
                    metadata={"semantic_model": "v0.9"},
                )
            )

    @staticmethod
    def _link_relationships(source: ReunionDatabase, database: FoundationDatabase) -> None:
        for family_id, semantic_family in sorted(source.families.items()):
            family = database.family(family_id)

            for spouse_id in semantic_family.spouse_ids:
                spouse = database.people.find(spouse_id)
                if spouse is None:
                    continue
                family.add_spouse(spouse)
                if all(existing.id != family.id for existing in spouse.spouse_families):
                    spouse.spouse_families.append(family)

            for child_id in semantic_family.child_ids:
                child = database.people.find(child_id)
                if child is None:
                    continue
                family.add_child(child)
                if all(existing.id != family.id for existing in child.parent_families):
                    child.parent_families.append(family)

    @staticmethod
    def _build_sources(source: ReunionDatabase, database: FoundationDatabase) -> None:
        for source_id, item in sorted(source.sources.items()):
            database.add_source(
                FoundationSource(
                    object_id=source_id,
                    title=item.title,
                    source_type=item.source_type,
                    repository_id=item.repository_id,
                    source_offset=item.raw_offset,
                    decode_status=item.decode_status,
                    metadata={"semantic_model": "v0.9"},
                )
            )

    @staticmethod
    def _note_sequence(source: ReunionDatabase):
        note_id = 1
        for person_id, person in sorted(source.people.items()):
            for note_index, note in enumerate(person.notes):
                yield note_id, "person", person_id, note_index, note
                note_id += 1
        for family_id, family in sorted(source.families.items()):
            for note_index, note in enumerate(family.notes):
                yield note_id, "family", family_id, note_index, note
                note_id += 1

    def _build_notes(self, source: ReunionDatabase, database: FoundationDatabase) -> None:
        for note_id, owner_type, owner_id, note_index, note in self._note_sequence(source):
            foundation_note = FoundationNote(
                object_id=note_id,
                note_type=note.note_type,
                text=note.text,
                format=note.format,
                owner_type=owner_type,
                owner_id=owner_id,
                source_offset=note.raw_offset,
                decode_status=note.decode_status,
                metadata={
                    "semantic_model": "v0.9",
                    "note_index": note_index,
                },
            )
            database.add_note(foundation_note)
            if owner_type == "person":
                database.person(owner_id).notes.append(foundation_note)
            else:
                database.family(owner_id).notes.append(foundation_note)

    @staticmethod
    def _event_id_sequence(source: ReunionDatabase):
        event_id = 1
        for person_id, person in sorted(source.people.items()):
            for event_index, event in enumerate(person.events):
                yield event_id, "person", person_id, event_index, event
                event_id += 1
        for family_id, family in sorted(source.families.items()):
            for event_index, event in enumerate(family.events):
                yield event_id, "family", family_id, event_index, event
                event_id += 1

    def _build_events(
        self,
        source: ReunionDatabase,
        database: FoundationDatabase,
    ) -> dict[tuple[str, int, int], FoundationEvent]:
        event_map: dict[tuple[str, int, int], FoundationEvent] = {}

        for event_id, owner_type, owner_id, event_index, semantic_event in self._event_id_sequence(source):
            place = (
                database.places.find(semantic_event.place_id)
                if semantic_event.place_id is not None
                else None
            )

            event = FoundationEvent(
                object_id=event_id,
                event_type=semantic_event.event_type,
                date_text=semantic_event.date.display if semantic_event.date is not None else None,
                place=place,
                place_text=semantic_event.place,
                memo=semantic_event.memo,
                owner_type=owner_type,
                owner_id=owner_id,
                source_offset=semantic_event.raw_offset,
                decode_status=semantic_event.decode_status,
                media_keys=list(semantic_event.media_ids),
                metadata={
                    "semantic_model": "v0.9",
                    "event_index": event_index,
                    "place_id": semantic_event.place_id,
                },
            )
            database.add_event(event)
            event_map[(owner_type, owner_id, event_index)] = event

            if owner_type == "person":
                database.person(owner_id).events.append(event)
            else:
                database.family(owner_id).events.append(event)

        return event_map

    @staticmethod
    def _media_sequence(source: ReunionDatabase):
        media_id = 1
        for media_key, media in sorted(source.media.items()):
            yield media_id, media_key, media
            media_id += 1

    def _build_media(self, source: ReunionDatabase, database: FoundationDatabase) -> None:
        for media_id, media_key, item in self._media_sequence(source):
            foundation_media = FoundationMedia(
                object_id=media_id,
                media_key=media_key,
                owner_type=item.owner_type,
                owner_id=item.owner_id,
                fingerprint=item.fingerprint,
                filename=item.filename,
                original_path=item.original_path,
                media_type=item.media_type,
                caption=item.caption,
                description=item.description,
                filename_link_status=item.filename_link_status,
                metadata_link_status=item.metadata_link_status,
                metadata={"semantic_model": "v0.9"},
            )
            database.add_media(foundation_media)

            if item.owner_type == "person":
                owner = database.people.find(item.owner_id)
                if owner is not None:
                    owner.media.append(foundation_media)
            elif item.owner_type == "family":
                owner = database.families.find(item.owner_id)
                if owner is not None:
                    owner.media.append(foundation_media)

    @staticmethod
    def _citation_sequence(source: ReunionDatabase):
        citation_id = 1
        for person_id, person in sorted(source.people.items()):
            for event_index, event in enumerate(person.events):
                for citation_index, citation in enumerate(event.citations):
                    yield (
                        citation_id,
                        "person",
                        person_id,
                        event_index,
                        citation_index,
                        citation,
                    )
                    citation_id += 1

        for family_id, family in sorted(source.families.items()):
            for event_index, event in enumerate(family.events):
                for citation_index, citation in enumerate(event.citations):
                    yield (
                        citation_id,
                        "family",
                        family_id,
                        event_index,
                        citation_index,
                        citation,
                    )
                    citation_id += 1

    def _build_citations(
        self,
        source: ReunionDatabase,
        database: FoundationDatabase,
        event_map: dict[tuple[str, int, int], FoundationEvent],
    ) -> None:
        for (
            citation_id,
            owner_type,
            owner_id,
            event_index,
            citation_index,
            citation,
        ) in self._citation_sequence(source):
            event = event_map[(owner_type, owner_id, event_index)]
            linked_source = database.sources.find(citation.source_id)

            foundation_citation = FoundationCitation(
                object_id=citation_id,
                source=linked_source,
                source_id=citation.source_id,
                source_title=citation.source_title,
                detail=citation.detail,
                owner_type=owner_type,
                owner_id=owner_id,
                event_id=event.id,
                source_offset=citation.raw_offset,
                decode_status=citation.decode_status,
                metadata={
                    "semantic_model": "v0.9",
                    "event_index": event_index,
                    "citation_index": citation_index,
                },
            )
            database.add_citation(foundation_citation)
            event.citations.append(foundation_citation)

            if linked_source is not None:
                linked_source.citations.append(foundation_citation)

            if owner_type == "person":
                database.person(owner_id).citations.append(foundation_citation)
            else:
                database.family(owner_id).citations.append(foundation_citation)
