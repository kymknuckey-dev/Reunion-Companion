from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class RelationshipEdge:
    """One directional step between two people."""

    from_id: int
    to_id: int
    relation: str
    family_id: int | None = None


@dataclass(slots=True)
class RelationshipPath:
    """Shortest decoded path between two people."""

    from_id: int
    to_id: int
    person_ids: list[int]
    edges: list[RelationshipEdge]
    label: str
    blood_relationship: str | None = None
    common_ancestor_ids: list[int] = field(default_factory=list)
    generation_distances: tuple[int, int] | None = None
    uses_spouse_link: bool = False

    @property
    def distance(self) -> int:
        return len(self.edges)


@dataclass(slots=True, frozen=True)
class GenerationPerson:
    person_id: int
    generations: int


@dataclass(slots=True)
class RelationshipComponent:
    component_id: int
    person_ids: list[int]
