from pathlib import Path

import pytest

from reunion_companion.parser import BinaryReader, ReunionFormatError


def test_missing_path() -> None:
    with pytest.raises(FileNotFoundError):
        BinaryReader("/definitely/not/here").inspect()


def test_unrecognised_directory(tmp_path: Path) -> None:
    with pytest.raises(ReunionFormatError):
        BinaryReader(tmp_path).inspect()


def test_reunion14_package(tmp_path: Path) -> None:
    main_file = tmp_path / "familyfile.familydata"
    main_file.write_bytes(b"probe")

    package = BinaryReader(tmp_path).inspect()

    assert package.version == "14+"
    assert package.main_data_size == 5
