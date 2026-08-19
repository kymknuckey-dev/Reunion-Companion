from reunion_companion.companion import publishing_v11 as pub


def test_photo_pair_cards_stretch_across_printable_width_for_true_centering():
    css=pub.PRO_CSS
    start=css.index(".photo-page .media-card {")
    scoped=css[start:start+400]
    assert "width:100%" in scoped
    assert "justify-self:stretch" in scoped
    assert "box-sizing:border-box" in scoped


def test_pass6_preserves_successful_orientation_sizes_and_no_crop():
    css=pub.PRO_CSS
    assert "max-height:106mm !important" in css
    assert "max-height:91mm !important" in css
    assert "object-fit:contain !important" in css


def test_original_file_links_are_removed_from_publication_renderer():
    source=__import__("inspect").getsource(pub)
    assert "Open original PDF" not in source
    assert "Open original document" not in source
