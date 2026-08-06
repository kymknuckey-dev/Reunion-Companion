from reunion_companion.sources import extract_sources_from_data


def _source_record(source_id: int, title: str) -> bytes:
    title_raw = title.encode()
    payload = (
        (len(title_raw) + 4).to_bytes(2, "little")
        + b"\x14\x00"
        + title_raw
    )
    declared_length = len(payload) + 4
    return (
        b"\x01\x00"
        + b"\x05\x03\x02\x01"
        + declared_length.to_bytes(4, "little")
        + source_id.to_bytes(4, "little")
        + payload
    )


def test_extract_free_form_source() -> None:
    sources = extract_sources_from_data(
        _source_record(1, "Test Probe Birth Certificate")
    )
    assert len(sources) == 1
    assert sources[0].source_id == 1
    assert sources[0].title == "Test Probe Birth Certificate"
