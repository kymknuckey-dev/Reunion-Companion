"""Pass 5 compatibility marker.

Pass 6 deliberately supersedes Pass 5's fixed 108mm row geometry and
portrait-only allowance. These assertions preserve the intended invariants
without requiring the rejected Pass 5 implementation.
"""
from reunion_companion.companion import publishing_v11 as pub

CSS = pub.PRO_CSS


def test_portrait_pair_images_get_larger_allowance_without_cropping():
    start = CSS.index(".photo-page figure.media-card.media-portrait img,")
    end = CSS.index("/* Landscape sizing", start)
    scoped = CSS[start:end]
    assert "max-height:106mm !important" in scoped
    assert "object-fit:contain !important" in scoped


def test_landscape_pair_images_keep_pass_4_size():
    start = CSS.index(".photo-page figure.media-card.media-landscape img")
    scoped = CSS[start:start + 300]
    assert "max-height:91mm !important" in scoped
    assert "object-fit:contain !important" in scoped


def test_two_photo_page_geometry_is_unchanged():
    # Pass 6 replaces the rejected 108mm Pass 5 rows with two 113mm slots,
    # each reserving 7mm for an unclipped caption.
    assert "grid-template-rows:113mm 113mm" in CSS
    assert "grid-template-rows:minmax(0,106mm) 7mm" in CSS
