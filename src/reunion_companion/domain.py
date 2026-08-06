from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

from .models import Event
from .records import TreeExtraction, extract_tree


@dataclass(slots=True)
class PersonProfile:
    id: int
    given: str
    surname: str
    display: str
    sex: str | None
    events: list[Event] = field(default_factory=list)
    parent_family_ids: list[int] = field(default_factory=list)
    spouse_ids: list[int] = field(default_factory=list)
    parent_ids: list[int] = field(default_factory=list)
    child_ids: list[int] = field(default_factory=list)


@dataclass(slots=True)
class FamilyUnit:
    id: int
    spouse_ids: list[int] = field(default_factory=list)
    child_ids: list[int] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)


@dataclass(slots=True)
class GenealogyTree:
    package_path: str
    version: str
    people: dict[int, PersonProfile]
    families: dict[int, FamilyUnit]
    warnings: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "package_path": self.package_path,
            "version": self.version,
            "people": {
                str(person_id): asdict(person)
                for person_id, person in sorted(self.people.items())
            },
            "families": {
                str(family_id): asdict(family)
                for family_id, family in sorted(self.families.items())
            },
            "warnings": list(self.warnings),
        }

    def get_person(self, person_id: int) -> PersonProfile:
        try:
            return self.people[person_id]
        except KeyError as exc:
            raise KeyError(f"Person {person_id} was not found") from exc

    def find_people(self, query: str) -> list[PersonProfile]:
        needle = query.casefold().strip()
        if not needle:
            return []
        return [
            person
            for person in self.people.values()
            if needle in person.display.casefold()
            or needle in person.given.casefold()
            or needle in person.surname.casefold()
        ]

    def get_family(self, family_id: int) -> FamilyUnit:
        try:
            return self.families[family_id]
        except KeyError as exc:
            raise KeyError(f"Family {family_id} was not found") from exc

    def person_name(self, person_id: int) -> str:
        person = self.people.get(person_id)
        return person.display if person else f"Person {person_id}"


def build_genealogy_tree(extraction: TreeExtraction) -> GenealogyTree:
    people = {
        item.record_id: PersonProfile(
            id=item.record_id,
            given=item.given,
            surname=item.surname,
            display=item.display,
            sex=item.sex,
            events=list(item.events),
            parent_family_ids=list(item.parent_family_ids),
        )
        for item in extraction.people
    }

    families = {
        item.family_id: FamilyUnit(
            id=item.family_id,
            spouse_ids=list(item.spouse_ids),
            child_ids=list(item.child_ids),
            events=list(item.events),
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

    return GenealogyTree(
        package_path=extraction.package_path,
        version=extraction.version,
        people=people,
        families=families,
        warnings=list(extraction.warnings),
    )


def load_genealogy_tree(package_path: str | Path) -> GenealogyTree:
    return build_genealogy_tree(extract_tree(package_path))
