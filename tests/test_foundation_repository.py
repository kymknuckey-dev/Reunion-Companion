import pytest

from reunion_companion.foundation import (
    DuplicateObjectError,
    FoundationPerson,
    ObjectNotFoundError,
    Repository,
)


def _person(person_id: int, given: str) -> FoundationPerson:
    return FoundationPerson(object_id=person_id, given=given, surname="Probe")


def test_repository_add_get_iterate_and_count() -> None:
    repo: Repository[FoundationPerson] = Repository()
    first = repo.add(_person(1, "Test"))
    second = repo.add(_person(2, "Mary"))

    assert repo.get(1) is first
    assert repo.find(2) is second
    assert repo.ids() == [1, 2]
    assert repo.all() == [first, second]
    assert list(repo) == [first, second]
    assert repo.count == 2
    assert len(repo) == 2
    assert repo.is_empty is False


def test_repository_rejects_duplicate_identifier() -> None:
    repo: Repository[FoundationPerson] = Repository([_person(1, "Test")])
    with pytest.raises(DuplicateObjectError):
        repo.add(_person(1, "Other"))


def test_repository_can_replace_in_controlled_workflow() -> None:
    repo: Repository[FoundationPerson] = Repository([_person(1, "Test")])
    replacement = _person(1, "Replacement")
    repo.add(replacement, replace=True)
    assert repo.get(1) is replacement


def test_repository_missing_get_and_remove_raise() -> None:
    repo: Repository[FoundationPerson] = Repository()
    with pytest.raises(ObjectNotFoundError):
        repo.get(99)
    with pytest.raises(ObjectNotFoundError):
        repo.remove(99)


def test_repository_remove_and_membership() -> None:
    person = _person(1, "Test")
    repo: Repository[FoundationPerson] = Repository([person])

    assert 1 in repo
    removed = repo.remove(1)
    assert removed is person
    assert 1 not in repo
    assert repo.is_empty is True
