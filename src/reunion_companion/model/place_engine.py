from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class PlaceUsage:
    place_id: int
    place_name: str
    owner_type: str
    owner_id: int
    owner_name: str
    event_type: str
    event_index: int
    date_display: str | None = None


@dataclass(slots=True)
class PlaceSummary:
    place_id: int
    name: str
    usage_count: int
    person_event_count: int
    family_event_count: int
    people_ids: list[int] = field(default_factory=list)
    family_ids: list[int] = field(default_factory=list)
    event_types: dict[str, int] = field(default_factory=dict)
