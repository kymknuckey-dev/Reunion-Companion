from pathlib import Path

from reunion_companion.media import extract_media


def test_extract_single_person_media(tmp_path: Path) -> None:
    package = tmp_path / "Probe.familyfile14"
    package.mkdir()
    main = package / "familyfile.familydata"
    main.write_bytes(
        b"ProbePortrait.jpg\x00"
        b"/users/kym/documents/reunion files/media/photos/probeportrait.jpg\x00"
    )
    (package / "familyfile.signature").write_bytes(b"probe")
    small = package / "thumbnails" / "thumbnails_small"
    large = package / "thumbnails" / "thumbnails_large"
    small.mkdir(parents=True)
    large.mkdir(parents=True)
    (small / "p1-8f4821-200.jpg").write_bytes(b"small")
    (large / "p1-8f4821-1000.jpg").write_bytes(b"large")

    items = extract_media(package)

    assert len(items) == 1
    assert items[0].owner_type == "person"
    assert items[0].owner_id == 1
    assert items[0].fingerprint == "8f4821"
    assert items[0].filename == "ProbePortrait.jpg"
    assert [item.size_hint for item in items[0].thumbnails] == [200, 1000]
