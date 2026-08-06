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


def test_extract_two_person_media_in_owner_order(tmp_path: Path) -> None:
    package = tmp_path / "Probe.familyfile14"
    package.mkdir()
    main = package / "familyfile.familydata"
    main.write_bytes(
        b"ProbePortrait.jpg\x00"
        b"/users/kym/documents/reunion files/media/photos/probeportrait.jpg\x00"
        b"MaryProbePortrait.jpg\x00"
        b"/users/kym/documents/reunion files/media/photos/maryprobeportrait.jpg\x00"
    )
    (package / "familyfile.signature").write_bytes(b"probe")
    small = package / "thumbnails" / "thumbnails_small"
    large = package / "thumbnails" / "thumbnails_large"
    small.mkdir(parents=True)
    large.mkdir(parents=True)
    for name in (
        "p1-8f4821-200.jpg",
        "p2-90226f-200.jpg",
    ):
        (small / name).write_bytes(b"small")
    for name in (
        "p1-8f4821-1000.jpg",
        "p2-90226f-1000.jpg",
    ):
        (large / name).write_bytes(b"large")

    items = extract_media(package)

    assert [(item.owner_id, item.filename) for item in items] == [
        (1, "ProbePortrait.jpg"),
        (2, "MaryProbePortrait.jpg"),
    ]
    assert [item.fingerprint for item in items] == ["8f4821", "90226f"]
    assert all(
        item.filename_link_status == "decoded-ordered-controlled-probes"
        for item in items
    )


def test_extract_media_description_and_comment(tmp_path: Path) -> None:
    package = tmp_path / "Probe.familyfile14"
    package.mkdir()
    main = package / "familyfile.familydata"
    main.write_bytes(
        b"ProbePortrait.jpg\x00"
        b"/users/kym/media/probeportrait.jpg\x00"
        b"MaryProbePortrait.jpg\x00"
        b"/users/kym/media/maryprobeportrait.jpg\x00"
        b"\x00\x00Portrait of Mary Probebook"
        b"\x00\x00Added for Reunion Companion media metadata testing."
        + (b"\x00" * 16)
    )
    (package / "familyfile.signature").write_bytes(b"probe")
    small = package / "thumbnails" / "thumbnails_small"
    large = package / "thumbnails" / "thumbnails_large"
    small.mkdir(parents=True)
    large.mkdir(parents=True)
    for name in ("p1-8f4821-200.jpg", "p2-90226f-200.jpg"):
        (small / name).write_bytes(b"small")
    for name in ("p1-8f4821-1000.jpg", "p2-90226f-1000.jpg"):
        (large / name).write_bytes(b"large")

    items = extract_media(package)

    assert items[0].description is None
    assert items[1].description == "Portrait of Mary Probe"
    assert items[1].caption == (
        "Added for Reunion Companion media metadata testing."
    )
    assert items[1].metadata_link_status == (
        "decoded-single-metadata-controlled-probe"
    )
