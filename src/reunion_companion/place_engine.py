from __future__ import annotations

from collections import Counter

from .event_engine import EventEngine, event_definition
from .model import Place, PlaceSummary, PlaceUsage, ReunionDatabase


class PlaceEngine:
    """Search and usage analysis for decoded Reunion places."""

    def __init__(self, database: ReunionDatabase):
        self.database = database
        self.events = EventEngine(database)

    def all_places(self) -> list[Place]:
        return sorted(
            self.database.places.values(),
            key=lambda place: (place.name.casefold(), place.id),
        )

    def find(self, query: str) -> list[Place]:
        needle = query.casefold().strip()
        if not needle:
            return []
        return [
            place
            for place in self.all_places()
            if needle in place.name.casefold()
        ]

    def usages(self, place_id: int) -> list[PlaceUsage]:
        place = self.database.places.get(place_id)
        if place is None:
            raise KeyError(f"Place {place_id} was not found")

        result: list[PlaceUsage] = []
        for occurrence in self.events.all_events():
            event = occurrence.event
            if event.place_id != place_id:
                continue
            result.append(
                PlaceUsage(
                    place_id=place_id,
                    place_name=place.name,
                    owner_type=occurrence.owner_type,
                    owner_id=occurrence.owner_id,
                    owner_name=occurrence.owner_name,
                    event_type=event.event_type,
                    event_index=occurrence.event_index,
                    date_display=event.date.display if event.date else None,
                )
            )
        return result

    def summary(self, place_id: int) -> PlaceSummary:
        place = self.database.places.get(place_id)
        if place is None:
            raise KeyError(f"Place {place_id} was not found")

        usages = self.usages(place_id)
        person_ids = sorted({
            usage.owner_id
            for usage in usages
            if usage.owner_type == "person"
        })

        # Include people linked to family-owned events such as Marriage.
        for usage in usages:
            if usage.owner_type != "family":
                continue
            family = self.database.families.get(usage.owner_id)
            if family is None:
                continue
            person_ids.extend(
                person_id
                for person_id in family.spouse_ids
                if person_id not in person_ids
            )

        family_ids = sorted({
            usage.owner_id
            for usage in usages
            if usage.owner_type == "family"
        })
        counts = Counter(usage.event_type for usage in usages)

        return PlaceSummary(
            place_id=place_id,
            name=place.name,
            usage_count=len(usages),
            person_event_count=sum(u.owner_type == "person" for u in usages),
            family_event_count=sum(u.owner_type == "family" for u in usages),
            people_ids=sorted(person_ids),
            family_ids=family_ids,
            event_types=dict(sorted(counts.items())),
        )

    def summaries(self) -> list[PlaceSummary]:
        return [self.summary(place.id) for place in self.all_places()]

    def unused_places(self) -> list[Place]:
        return [
            place
            for place in self.all_places()
            if not self.usages(place.id)
        ]

    def coverage(self) -> dict[str, object]:
        summaries = self.summaries()
        linked = [summary for summary in summaries if summary.usage_count]
        unused = [summary for summary in summaries if not summary.usage_count]

        event_place_links = sum(summary.usage_count for summary in summaries)
        events = self.events.all_events()
        events_with_place = sum(bool(item.event.place) for item in events)
        events_with_place_id = sum(item.event.place_id is not None for item in events)

        return {
            "total_places": len(summaries),
            "used_places": len(linked),
            "unused_places": len(unused),
            "event_place_links": event_place_links,
            "events_total": len(events),
            "events_with_place_name": events_with_place,
            "events_with_place_id": events_with_place_id,
            "hierarchy_status": "not-decoded",
            "coordinates_status": "not-decoded",
            "notes_status": "not-decoded",
            "media_status": "not-decoded",
            "citations_status": "not-decoded",
        }

    def people_at_place(self, place_id: int) -> list[int]:
        return self.summary(place_id).people_ids

    def events_at_place(self, place_id: int):
        return [
            item
            for item in self.events.all_events()
            if item.event.place_id == place_id
        ]
