"""Build Foundation objects from the verified v0.9 semantic model.

This is an adapter layer, not a binary decoder. It deliberately consumes the
existing ``reunion_companion.model.ReunionDatabase`` so Alpha 4 can be proven
against real Reunion data without changing any established decoder path.
"""

from __future__ import annotations

from dataclasses import dataclass

from reunion_companion.model import ReunionDatabase

from .database import FoundationDatabase
from .event import FoundationEvent
from .family import FoundationFamily
from .person import FoundationPerson
from .place import FoundationPlace


@dataclass(slots=True)
class FoundationBuildReport:
    """Counts and diagnostics produced by one semantic-to-foundation build."""

    people: int
    families: int
    events: int
    places: int
    warnings: int

    def to_dict(self) -> dict[str, int]:
        return {
            "people": self.people,
            "families": self.families,
            "events": self.events,
            "places": self.places,
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
        self._build_events(source, database)
        database.rebuild_indexes()
        return database

    def build_with_report(
        self,
        source: ReunionDatabase,
    ) -> tuple[FoundationDatabase, FoundationBuildReport]:
        database = self.build(source)
        counts = database.object_counts
        report = FoundationBuildReport(
            people=counts["people"],
            families=counts["families"],
            events=counts["events"],
            places=counts["places"],
            warnings=len(database.warnings),
        )
        return database, report

    @staticmethod
    def _build_places(
        source: ReunionDatabase,
        database: FoundationDatabase,
    ) -> None:
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
    def _build_people(
        source: ReunionDatabase,
        database: FoundationDatabase,
    ) -> None:
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
    def _build_families(
        source: ReunionDatabase,
        database: FoundationDatabase,
    ) -> None:
        for family_id in sorted(source.families):
            database.add_family(
                FoundationFamily(
                    object_id=family_id,
                    metadata={"semantic_model": "v0.9"},
                )
            )

    @staticmethod
    def _link_relationships(
        source: ReunionDatabase,
        database: FoundationDatabase,
    ) -> None:
        for family_id, semantic_family in sorted(source.families.items()):
            family = database.family(family_id)

            for spouse_id in semantic_family.spouse_ids:
                spouse = database.people.find(spouse_id)
                if spouse is None:
                    continue
                family.add_spouse(spouse)
                if all(
                    existing.id != family.id
                    for existing in spouse.spouse_families
                ):
                    spouse.spouse_families.append(family)

            for child_id in semantic_family.child_ids:
                child = database.people.find(child_id)
                if child is None:
                    continue
                family.add_child(child)
                if all(
                    existing.id != family.id
                    for existing in child.parent_families
                ):
                    child.parent_families.append(family)

    @staticmethod
    def _event_id_sequence(source: ReunionDatabase):
        """Yield deterministic event IDs and semantic events.

        IDs are Foundation-local. They are deterministic for a given semantic
        database because owners and event positions are traversed in sorted
        owner-ID order.
        """
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
    ) -> None:
        for (
            event_id,
            owner_type,
            owner_id,
            event_index,
            semantic_event,
        ) in self._event_id_sequence(source):
            place = (
                database.places.find(semantic_event.place_id)
                if semantic_event.place_id is not None
                else None
            )

            event = FoundationEvent(
                object_id=event_id,
                event_type=semantic_event.event_type,
                date_text=(
                    semantic_event.date.display
                    if semantic_event.date is not None
                    else None
                ),
                place=place,
                place_text=semantic_event.place,
                memo=semantic_event.memo,
                owner_type=owner_type,
                owner_id=owner_id,
                source_offset=semantic_event.raw_offset,
                decode_status=semantic_event.decode_status,
                metadata={
                    "semantic_model": "v0.9",
                    "event_index": event_index,
                    "place_id": semantic_event.place_id,
                },
            )
            database.add_event(event)

            if owner_type == "person":
                database.person(owner_id).events.append(event)
            else:
                database.family(owner_id).events.append(event)
