from pathlib import Path
import tempfile

from reunion_companion.discovery.differential_verification import (
    byte_differences,
    compare_packages_differential,
    result_document,
)


def test_single_byte_replacement_is_detected():
    before = bytes.fromhex("01 02 03 04 05")
    after = bytes.fromhex("01 02 FF 04 05")
    spans = byte_differences(before, after)
    assert len(spans) == 1
    assert spans[0].tag == "replace"
    assert spans[0].before_start == 2
    assert "03" in spans[0].before_hex
    assert "ff" in spans[0].after_hex.lower()


def test_insertion_does_not_mark_tail_as_changed():
    before = b"ABCDEF"
    after = b"ABCXYZDEF"
    spans = byte_differences(before, after)
    assert len(spans) == 1
    assert spans[0].tag == "insert"
    assert spans[0].after_length == 3


def test_package_diff_detects_raw_change_without_structural_stack():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        b = root / "Before.familyfile14"
        a = root / "After.familyfile14"
        b.mkdir(); a.mkdir()
        (b / "familyfile.familydata").write_bytes(b"0123456789")
        (a / "familyfile.familydata").write_bytes(b"01234X6789")
        result = compare_packages_differential(b, a, declared_change="Birth Date")
        assert result.raw_changed is True
        assert result.byte_spans
        assert result.class_deltas == ()
        doc = result_document(result)
        assert doc["build"] == 14
        assert doc["raw_changed"] is True
