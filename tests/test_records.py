from reunion_companion.records import build_families, extract_structured_people


def _person_record(
    record_id: int,
    given: str,
    surname: str,
    sex_code: int,
    parent_family: int | None = None,
) -> bytes:
    payload = bytearray()
    payload += b"\x00\x1b\x00" + sex_code.to_bytes(2, "little")
    given_raw = given.encode()
    payload += (len(given_raw) + 4).to_bytes(2, "little") + b"\x1e\x00" + given_raw
    surname_raw = surname.encode()
    payload += (len(surname_raw) + 4).to_bytes(2, "little") + b"\x23\x00" + surname_raw
    if parent_family is not None:
        payload += b"\x08\x00\x3c\x00" + parent_family.to_bytes(4, "little")

    declared_length = len(payload) + 4
    return (
        b"\x01\x00"
        + b"\x05\x03\x02\x01"
        + declared_length.to_bytes(4, "little")
        + record_id.to_bytes(4, "little")
        + payload
    )


def test_extract_structured_people() -> None:
    data = (
        _person_record(1, "Test", "Probe", 1)
        + _person_record(2, "Mary", "Probe", 2)
        + _person_record(3, "Baby", "Probe", 1, parent_family=1)
    )
    people = extract_structured_people(data)

    assert [person.record_id for person in people] == [1, 2, 3]
    assert [person.sex for person in people] == ["male", "female", "male"]
    assert people[2].parent_family_ids == [1]


def test_build_simple_family() -> None:
    data = (
        _person_record(1, "Test", "Probe", 1)
        + _person_record(2, "Mary", "Probe", 2)
        + _person_record(3, "Baby", "Probe", 1, parent_family=1)
    )
    people = extract_structured_people(data)
    families = build_families(people, family_slots=1)

    assert families[0].spouse_ids == [1, 2]
    assert families[0].child_ids == [3]
    assert families[0].spouse_link_status == "inferred-controlled-pattern"
