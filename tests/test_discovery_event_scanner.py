from reunion_companion.discovery import (
    cluster_event_signatures,
    scan_event_observations,
)


MAGIC = b"\x05\x03\x02\x01"
DATE_MARKER = b"\x0a\x00\x08\x00\x00\x00"


def _text_field(tag: int, text: str) -> bytes:
    raw = text.encode("utf-8")
    return (len(raw) + 4).to_bytes(2, "little") + tag.to_bytes(2, "little") + raw


def _record(record_id: int, body: bytes) -> bytes:
    payload_length = max(16, 4 + len(body))
    padded_body = body + (b"\x00" * max(0, payload_length - 4 - len(body)))
    return (
        b"\x00\x00"
        + MAGIC
        + payload_length.to_bytes(4, "little")
        + record_id.to_bytes(4, "little")
        + padded_body
    )


def test_event_scanner_observes_multiple_dates_in_named_person_record() -> None:
    # Valid packed dates found through the established date decoder.
    raw_1925 = bytes.fromhex("98 15 1B 00")
    raw_2000 = bytes.fromhex("C8 41 3C 00")

    body = (
        _text_field(0x001E, "Test")
        + _text_field(0x0023, "Probe")
        + b"\xe8\x03" + b"\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa"
        + DATE_MARKER + b"\x00" + raw_1925
        + b"[[pt:1]]"
        + b"\x10\x27" + b"\xaa\xbb\xcc\xdd\xee\xff\x01\x02\x03\x04"
        + DATE_MARKER + b"\x00" + raw_2000
    )
    data = _record(1, body)

    observations, named = scan_event_observations(data)

    assert named == 1
    assert len(observations) == 2
    assert observations[0].person_id == 1
    assert observations[0].person_name == "Test Probe"
    assert observations[0].place_token == "[[pt:1]]"
    assert observations[0].signature != observations[1].signature


def test_signature_clustering_groups_identical_layouts() -> None:
    from reunion_companion.discovery.event_scanner import EventObservation

    base = dict(
        person_name="Test Probe",
        record_offset=0,
        record_length=100,
        marker_offset=50,
        raw_date_offset=57,
        qualifier=0,
        place_token=None,
        memo_candidate=False,
        context_hex="00",
    )
    observations = [
        EventObservation(person_id=1, date_display="1 Jan 1925", signature="aa bb", **base),
        EventObservation(person_id=2, date_display="2 Jan 1925", signature="aa bb", **base),
        EventObservation(person_id=3, date_display="3 Jan 1925", signature="cc dd", **base),
    ]

    clusters = cluster_event_signatures(observations)

    assert clusters[0].signature == "aa bb"
    assert clusters[0].count == 2
    assert clusters[1].count == 1
