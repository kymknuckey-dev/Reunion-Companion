from pathlib import Path

PUB = (Path(__file__).parents[1] / "src/reunion_companion/companion/publishing_v11.py").read_text()


def test_photo_pair_print_rule_overrides_legacy_single_photo_height():
    legacy = "figure.media-card.media-portrait img { max-height:198mm !important"
    paired = ".photo-page figure.media-card.media-portrait img,"
    assert legacy in PUB
    assert paired in PUB
    assert PUB.index(paired) > PUB.index(legacy)
    scoped = PUB[PUB.index(paired):PUB.index(".web-only", PUB.index(paired))]
    assert "max-height:106mm !important" in scoped
    assert "height:auto !important" in scoped
    assert "object-fit:contain !important" in scoped


def test_photo_pages_remain_two_vertical_slots_without_crop():
    assert "grid-template-rows:113mm 113mm" in PUB
    assert ".photo-page .media-card {" in PUB
    assert "overflow:visible" in PUB
    # The image itself must fit inside the slot, so overflow on the slot cannot crop it.
    assert ".photo-page .media-card img { display:block; width:auto; height:auto; max-width:100%; max-height:106mm; object-fit:contain;" in PUB
