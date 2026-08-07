from __future__ import annotations

from collections import deque
from dataclasses import asdict
from typing import Iterable

from .model import (
    GenerationPerson,
    RelationshipComponent,
    RelationshipEdge,
    RelationshipPath,
    ReunionDatabase,
)


def ordinal(number: int) -> str:
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def ancestor_term(generations: int, *, reverse: bool = False) -> str:
    base = "child" if reverse else "parent"
    if generations == 1:
        return base
    if generations == 2:
        return "grandchild" if reverse else "grandparent"
    prefix = "great-" * (generations - 2)
    return prefix + ("grandchild" if reverse else "grandparent")


def sibling_term() -> str:
    return "sibling"


def cousin_term(degree: int, removed: int) -> str:
    if degree < 1:
        return sibling_term()
    label = f"{ordinal(degree)} cousin"
    if removed == 1:
        return label + " once removed"
    if removed > 1:
        return label + f" {removed} times removed"
    return label


class RelationshipEngine:
    """Genealogical graph operations over a decoded ReunionDatabase."""

    def __init__(self, database: ReunionDatabase):
        self.database = database
        self._adjacency = self._build_adjacency()

    def _build_adjacency(self) -> dict[int, list[RelationshipEdge]]:
        adjacency: dict[int, list[RelationshipEdge]] = {
            person_id: [] for person_id in self.database.people
        }

        def add(edge: RelationshipEdge) -> None:
            existing = adjacency.setdefault(edge.from_id, [])
            if edge not in existing:
                existing.append(edge)

        for family in self.database.families.values():
            for parent_id in family.spouse_ids:
                for child_id in family.child_ids:
                    if parent_id not in self.database.people or child_id not in self.database.people:
                        continue
                    add(RelationshipEdge(parent_id, child_id, "child", family.id))
                    add(RelationshipEdge(child_id, parent_id, "parent", family.id))

            for index, spouse_id in enumerate(family.spouse_ids):
                for other_id in family.spouse_ids[index + 1 :]:
                    if spouse_id not in self.database.people or other_id not in self.database.people:
                        continue
                    add(RelationshipEdge(spouse_id, other_id, "spouse", family.id))
                    add(RelationshipEdge(other_id, spouse_id, "spouse", family.id))

        for edges in adjacency.values():
            edges.sort(key=lambda edge: (edge.to_id, edge.relation))
        return adjacency

    def ancestors(
        self,
        person_id: int,
        max_generations: int | None = None,
    ) -> list[GenerationPerson]:
        self.database.get_person(person_id)
        found: dict[int, int] = {}
        queue: deque[tuple[int, int]] = deque([(person_id, 0)])

        while queue:
            current_id, generation = queue.popleft()
            if max_generations is not None and generation >= max_generations:
                continue
            for parent_id in self.database.get_person(current_id).parent_ids:
                next_generation = generation + 1
                previous = found.get(parent_id)
                if previous is None or next_generation < previous:
                    found[parent_id] = next_generation
                    queue.append((parent_id, next_generation))

        return [
            GenerationPerson(person_id=item_id, generations=generation)
            for item_id, generation in sorted(
                found.items(), key=lambda item: (item[1], self.database.person_name(item[0]))
            )
        ]

    def descendants(
        self,
        person_id: int,
        max_generations: int | None = None,
    ) -> list[GenerationPerson]:
        self.database.get_person(person_id)
        found: dict[int, int] = {}
        queue: deque[tuple[int, int]] = deque([(person_id, 0)])

        while queue:
            current_id, generation = queue.popleft()
            if max_generations is not None and generation >= max_generations:
                continue
            for child_id in self.database.get_person(current_id).child_ids:
                next_generation = generation + 1
                previous = found.get(child_id)
                if previous is None or next_generation < previous:
                    found[child_id] = next_generation
                    queue.append((child_id, next_generation))

        return [
            GenerationPerson(person_id=item_id, generations=generation)
            for item_id, generation in sorted(
                found.items(), key=lambda item: (item[1], self.database.person_name(item[0]))
            )
        ]

    def ancestor_distances(self, person_id: int) -> dict[int, int]:
        return {
            item.person_id: item.generations
            for item in self.ancestors(person_id)
        }

    def common_ancestors(
        self,
        first_id: int,
        second_id: int,
    ) -> list[tuple[int, int, int]]:
        first = self.ancestor_distances(first_id)
        second = self.ancestor_distances(second_id)

        # A person is also generation zero from themselves. This allows
        # ancestor/descendant relationships to be classified consistently.
        first[first_id] = 0
        second[second_id] = 0

        matches = [
            (ancestor_id, first[ancestor_id], second[ancestor_id])
            for ancestor_id in first.keys() & second.keys()
        ]
        return sorted(
            matches,
            key=lambda item: (
                max(item[1], item[2]),
                item[1] + item[2],
                self.database.person_name(item[0]),
            ),
        )

    def blood_relationship(
        self,
        first_id: int,
        second_id: int,
    ) -> tuple[str | None, list[int], tuple[int, int] | None]:
        if first_id == second_id:
            return "same person", [first_id], (0, 0)

        common = self.common_ancestors(first_id, second_id)
        if not common:
            return None, [], None

        best_max = max(common[0][1], common[0][2])
        best_sum = common[0][1] + common[0][2]
        nearest = [
            item for item in common
            if max(item[1], item[2]) == best_max and item[1] + item[2] == best_sum
        ]
        ancestor_ids = [item[0] for item in nearest]
        first_distance, second_distance = nearest[0][1], nearest[0][2]

        if first_distance == 0:
            # From first person's perspective: the second person is a descendant.
            label = ancestor_term(second_distance, reverse=True)
        elif second_distance == 0:
            # From first person's perspective: the second person is an ancestor.
            label = ancestor_term(first_distance, reverse=False)
        elif first_distance == 1 and second_distance == 1:
            label = sibling_term()
        else:
            degree = min(first_distance, second_distance) - 1
            removed = abs(first_distance - second_distance)
            label = cousin_term(degree, removed)

        return label, ancestor_ids, (first_distance, second_distance)

    def shortest_path(
        self,
        first_id: int,
        second_id: int,
        *,
        include_spouses: bool = True,
    ) -> RelationshipPath | None:
        self.database.get_person(first_id)
        self.database.get_person(second_id)

        if first_id == second_id:
            return RelationshipPath(
                from_id=first_id,
                to_id=second_id,
                person_ids=[first_id],
                edges=[],
                label="same person",
                blood_relationship="same person",
                common_ancestor_ids=[first_id],
                generation_distances=(0, 0),
            )

        queue: deque[int] = deque([first_id])
        previous: dict[int, tuple[int, RelationshipEdge] | None] = {first_id: None}

        while queue:
            current_id = queue.popleft()
            for edge in self._adjacency.get(current_id, []):
                if not include_spouses and edge.relation == "spouse":
                    continue
                if edge.to_id in previous:
                    continue
                previous[edge.to_id] = (current_id, edge)
                if edge.to_id == second_id:
                    queue.clear()
                    break
                queue.append(edge.to_id)

        if second_id not in previous:
            return None

        edges_reversed: list[RelationshipEdge] = []
        current = second_id
        while current != first_id:
            entry = previous[current]
            if entry is None:
                break
            prior, edge = entry
            edges_reversed.append(edge)
            current = prior

        edges = list(reversed(edges_reversed))
        person_ids = [first_id] + [edge.to_id for edge in edges]
        uses_spouse = any(edge.relation == "spouse" for edge in edges)
        blood_label, ancestors, distances = self.blood_relationship(first_id, second_id)

        if not include_spouses and blood_label is None:
            return None

        if len(edges) == 1:
            label = edges[0].relation
        elif blood_label and not uses_spouse:
            label = blood_label
        else:
            label = self.path_description(edges)

        return RelationshipPath(
            from_id=first_id,
            to_id=second_id,
            person_ids=person_ids,
            edges=edges,
            label=label,
            blood_relationship=blood_label,
            common_ancestor_ids=ancestors,
            generation_distances=distances,
            uses_spouse_link=uses_spouse,
        )

    @staticmethod
    def path_description(edges: Iterable[RelationshipEdge]) -> str:
        relations = [edge.relation for edge in edges]
        return " → ".join(relations) if relations else "same person"

    def connected_components(self) -> list[RelationshipComponent]:
        remaining = set(self.database.people)
        components: list[RelationshipComponent] = []

        while remaining:
            start = min(remaining)
            queue: deque[int] = deque([start])
            members: set[int] = {start}
            remaining.remove(start)

            while queue:
                current = queue.popleft()
                for edge in self._adjacency.get(current, []):
                    if edge.to_id in members:
                        continue
                    members.add(edge.to_id)
                    remaining.discard(edge.to_id)
                    queue.append(edge.to_id)

            components.append(
                RelationshipComponent(
                    component_id=len(components) + 1,
                    person_ids=sorted(members),
                )
            )

        return sorted(
            components,
            key=lambda component: (-len(component.person_ids), component.person_ids),
        )
