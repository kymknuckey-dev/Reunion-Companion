from reunion_companion.records import (
    build_families,
    extract_structured_families,
    extract_structured_people,
    extract_person_notes,
)


def _person_record(
    record_id: int,
    given: str,
    surname: str,
    sex_code: int,
    parent_family: int | None = None,
    birth_date: bytes | None = None,
    qualifier: int = 0,
    memo: str | None = None,
    place_id: int | None = None,
    citation_detail: str | None = None,
) -> bytes:
    payload = bytearray()
    payload += b"\x00\x1b\x00" + sex_code.to_bytes(2, "little")
    given_raw = given.encode()
    payload += (len(given_raw) + 4).to_bytes(2, "little") + b"\x1e\x00" + given_raw
    surname_raw = surname.encode()
    payload += (len(surname_raw) + 4).to_bytes(2, "little") + b"\x23\x00" + surname_raw
    if parent_family is not None:
        payload += b"\x08\x00\x3c\x00" + parent_family.to_bytes(4, "little")
    if birth_date is not None:
        payload += b"\xe8\x03"
        payload += b"\x0a\x00\x08\x00\x00\x00" + bytes([qualifier]) + birth_date
        if place_id is not None:
            token = f"[[pt:{place_id}]]".encode()
            payload += b"\x00\x00\x00" + token
        if memo:
            tag = b"[[pt:1]]"
            memo_raw = memo.encode()
            payload += tag + (len(memo_raw) + 4).to_bytes(4, "little") + memo_raw
        if citation_detail:
            detail_raw = citation_detail.encode()
            field_length = len(detail_raw) + 8
            total_length = 20 + len(detail_raw)
            inner_length = total_length - 4
            payload += total_length.to_bytes(4, "little")
            payload += inner_length.to_bytes(4, "little")
            payload += (1).to_bytes(4, "little")
            payload += field_length.to_bytes(2, "little")
            payload += (0xAEB6).to_bytes(2, "little")
            payload += (1).to_bytes(4, "little")
            payload += detail_raw

    declared_length = len(payload) + 4
    return (
        b"\x01\x00"
        + b"\x05\x03\x02\x01"
        + declared_length.to_bytes(4, "little")
        + record_id.to_bytes(4, "little")
        + payload
    )


def _family_record(family_id: int, spouse_a: int, spouse_b: int, marriage_date: bytes, place_id: int | None = None) -> bytes:
    payload = bytearray()
    payload += b"\x08\x00\x50\x00" + spouse_a.to_bytes(4, "little")
    payload += b"\x08\x00\x51\x00" + spouse_b.to_bytes(4, "little")
    payload += b"\x08\x00\x00\x00\x00" + marriage_date
    if place_id is not None:
        token = f"[[pt:{place_id}]]".encode()
        payload += b"\x00\x00\x00" + token
    declared_length = len(payload) + 4
    return (
        b"\x01\x00"
        + b"\x05\x03\x02\x01"
        + declared_length.to_bytes(4, "little")
        + family_id.to_bytes(4, "little")
        + payload
    )


def test_extract_structured_people_and_birth() -> None:
    data = (
        _person_record(
            1,
            "Test",
            "Probe",
            1,
            birth_date=bytes.fromhex("42 14 9B 0C"),
            memo="Probe birth memo",
            place_id=1,
            citation_detail="Certificate reference TP-1925-001",
        )
        + _person_record(2, "Mary", "Probe", 2)
        + _person_record(
            3,
            "Baby",
            "Probe",
            1,
            parent_family=1,
            birth_date=bytes.fromhex("40 E1 9B 16"),
            qualifier=0xA0,
        )
    )
    people = extract_structured_people(data)

    assert [person.record_id for person in people] == [1, 2, 3]
    assert people[0].events[0].date.display == "2 Jan 1925"
    assert people[0].events[0].memo == "Probe birth memo"
    assert people[0].events[0].place_id == 1
    assert people[0].events[0].citations[0].source_id == 1
    assert people[0].events[0].citations[0].detail == "Certificate reference TP-1925-001"
    assert people[2].events[0].date.display == "abt May 1976"
    assert people[2].parent_family_ids == [1]


def test_extract_family_spouses_and_marriage() -> None:
    data = _family_record(1, 1, 2, bytes.fromhex("C3 78 9B 0C"), place_id=2)
    families = extract_structured_families(data)

    assert len(families) == 1
    assert families[0].spouse_ids == [1, 2]
    assert families[0].spouse_link_status == "decoded"
    assert families[0].events[0].date.display == "3 Mar 1950"
    assert families[0].events[0].place_id == 2


def test_build_family_children() -> None:
    data = (
        _person_record(1, "Test", "Probe", 1)
        + _person_record(2, "Mary", "Probe", 2)
        + _person_record(3, "Baby", "Probe", 1, parent_family=1)
        + _family_record(1, 1, 2, bytes.fromhex("C3 78 9B 0C"))
    )
    people = extract_structured_people(data)
    decoded = extract_structured_families(data)
    families = build_families(people, decoded, family_slots=1)

    assert families[0].spouse_ids == [1, 2]
    assert families[0].child_ids == [3]


def test_extract_standalone_person_note() -> None:
    text = b"This is the Test Probe person note.\nIt contains family history information for Reunion Companion."
    payload = b"\xf5\x09ujq\x00\x00\x00talfa" + (b"\x00" * 7) + text
    declared_length = len(payload) + 4
    record = (
        b"\x04\x21"
        + b"\x05\x03\x02\x01"
        + declared_length.to_bytes(4, "little")
        + (1).to_bytes(4, "little")
        + payload
    )
    notes = extract_person_notes(record)
    assert notes[1][0].note_type == "person"
    assert notes[1][0].format == "plain"
    assert notes[1][0].text == text.decode()
