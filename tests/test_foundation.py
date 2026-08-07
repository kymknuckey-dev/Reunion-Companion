from dataclasses import dataclass

import pytest

from reunion_companion.foundation import FoundationObject, ObjectId, RecordLocation


@dataclass(slots=True, kw_only=True)
class ExampleObject(FoundationObject):
    label: str = ""


def test_object_id_accepts_non_negative_integer() -> None:
    identifier = ObjectId(42)
    assert int(identifier) == 42
    assert str(identifier) == "42"


def test_object_id_rejects_negative_values() -> None:
    with pytest.raises(ValueError):
        ObjectId(-1)


def test_object_id_coerce_preserves_instance() -> None:
    identifier = ObjectId(7)
    assert ObjectId.coerce(identifier) is identifier
    assert ObjectId.coerce(8) == ObjectId(8)


def test_record_location_reports_end_and_known_state() -> None:
    location = RecordLocation(offset=100, length=24)
    assert location.end == 124
    assert location.is_known is True
    assert RecordLocation().is_known is False


def test_record_location_rejects_negative_values() -> None:
    with pytest.raises(ValueError):
        RecordLocation(offset=-1, length=10)
    with pytest.raises(ValueError):
        RecordLocation(offset=10, length=-1)


def test_foundation_object_identity_and_change_tracking() -> None:
    item = ExampleObject(object_id=ObjectId(3), label="Probe")
    assert item.id == 3
    assert item.identity == "ExampleObject(3)"
    assert item.modified is False
    item.mark_modified()
    assert item.modified is True
    item.clear_modified()
    assert item.modified is False


def test_foundation_object_coerces_integer_identifier() -> None:
    item = ExampleObject(object_id=9)
    assert item.object_id == ObjectId(9)
    assert item.id == 9
