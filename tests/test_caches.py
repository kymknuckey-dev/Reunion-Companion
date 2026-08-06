from pathlib import Path

from reunion_companion.caches import (
    build_cache_summary,
    decode_fmnames,
    decode_index,
    decode_place_usage_count,
    decode_places,
    decode_surnames,
)


def test_decode_probe_given_names() -> None:
    data = bytes.fromhex(
        "3c0000003277707303000000180000002400000030000000"
        "0c0114004200727942616279"
        "0c0128004d0073744d617279"
        "0c0134005400000054657374"
    )
    cache = decode_fmnames(data)
    assert cache.declared_count == 3
    assert cache.values == ["Baby", "Mary", "Test"]


def test_decode_probe_places() -> None:
    data = bytes.fromhex(
        "69000000616863700200000000f2bda21800000040000000"
        "2800000001000000a606444102000000"
    ) + b"Adelaide Registry Office" + bytes.fromhex(
        "2900000002000000e706444101000000"
    ) + b"Adelaide, South Australia"
    cache = decode_places(data)
    assert cache.declared_count == 2
    assert cache.values == ["Adelaide Registry Office", "Adelaide, South Australia"]


def test_decode_probe_surname() -> None:
    data = bytes.fromhex("1800000031306e73102701000c700000") + b"Probe\x00\x00\x00"
    cache = decode_surnames(data)
    assert cache.declared_count == 1
    assert cache.values == ["Probe"]


def test_decode_probe_index() -> None:
    data = bytes.fromhex(
        "3c000000303963690300000001000000d68c28a907000000"
        "23380200000000001e380200000000000a18faffffffffff"
        "030000000200000001000000"
    )
    cache = decode_index(data)
    assert cache.primary_slots == 3
    assert cache.family_slots == 1
    assert cache.trailing_ids == [3, 2, 1]


def test_decode_place_usage_count() -> None:
    data = bytes.fromhex(
        "4400000068637570020000000100000000f2bda218000000"
        "01000000010000000000000001000000111c540018000000"
        "0100000002000000000000000100000022017500"
    )
    assert decode_place_usage_count(data) == 2


def test_build_cache_summary(tmp_path: Path) -> None:
    # Missing caches produce warnings rather than aborting inventory.
    summary = build_cache_summary(tmp_path)
    assert summary.given_names is None
    assert any("fmnames.cache" in warning for warning in summary.warnings)
