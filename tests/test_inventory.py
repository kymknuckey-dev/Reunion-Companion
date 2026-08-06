from pathlib import Path

from reunion_companion.inventory import build_inventory, extract_people


def test_extract_people_from_known_field_pattern() -> None:
    # Field lengths include the four-byte field header in current probe evidence.
    data = (
        b"prefix"
        + (8).to_bytes(2, "little")
        + b"\x1e\x00Test"
        + (9).to_bytes(2, "little")
        + b"\x23\x00PROBE"
        + b"suffix"
    )

    people = extract_people(data)

    assert len(people) == 1
    assert people[0].given == "Test"
    assert people[0].surname == "PROBE"
    assert people[0].display == "Test Probe"


def test_build_inventory_for_minimal_reunion14_package(tmp_path: Path) -> None:
    (tmp_path / "familyfile.familydata").write_bytes(b"plain data")
    (tmp_path / "places.cache").write_bytes(b"cache")
    thumbnails = tmp_path / "thumbnails" / "thumbnails_small"
    thumbnails.mkdir(parents=True)
    (thumbnails / "p1-abc-200.jpg").write_bytes(b"jpg")
    (thumbnails / "f1-def-200.jpg").write_bytes(b"jpg")

    inventory = build_inventory(tmp_path)

    assert inventory.version == "14+"
    assert inventory.main_data_size == 10
    assert inventory.total_files == 4
    assert inventory.thumbnails.total == 2
    assert inventory.thumbnails.person == 1
    assert inventory.thumbnails.family == 1
