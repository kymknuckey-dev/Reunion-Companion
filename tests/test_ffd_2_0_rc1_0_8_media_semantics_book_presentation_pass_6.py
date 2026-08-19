from reunion_companion.companion import publishing_v11 as pub

CSS=pub.PRO_CSS

def test_photo_pair_uses_explicit_image_and_caption_rows():
    assert "height:231mm" in CSS
    assert "grid-template-rows:113mm 113mm" in CSS
    assert "grid-template-rows:minmax(0,106mm) 7mm" in CSS
    assert "overflow:visible" in CSS


def test_portraits_can_grow_without_cropping():
    start=CSS.index(".photo-page figure.media-card.media-portrait img,")
    end=CSS.index("/* Landscape sizing", start)
    scoped=CSS[start:end]
    assert "max-height:106mm !important" in scoped
    assert "object-fit:contain !important" in scoped


def test_landscape_retains_pass_4_size():
    start=CSS.index(".photo-page figure.media-card.media-landscape img")
    scoped=CSS[start:start+300]
    assert "max-height:91mm !important" in scoped
    assert "object-fit:contain !important" in scoped


def test_caption_is_not_inside_clipping_container():
    assert ".photo-page .media-card figcaption { margin:0;" in CSS
    assert "max-width:100%; overflow:visible;" in CSS
