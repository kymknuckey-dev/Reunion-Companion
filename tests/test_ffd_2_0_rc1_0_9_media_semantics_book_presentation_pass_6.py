from reunion_companion.companion import publishing_v11 as pub


def test_photo_pair_cards_use_full_width_flex_centering():
    css=pub.PRO_CSS
    start=css.index(".photo-page .media-card {")
    scoped=css[start:start+500]
    assert "width:100%" in scoped
    assert "display:flex" in scoped
    assert "flex-direction:column" in scoped
    assert "align-items:center" in scoped
    assert "justify-content:flex-start" in scoped
    assert "display:grid" not in scoped


def test_photo_pair_captions_own_visible_full_width_row():
    css=pub.PRO_CSS
    start=css.index(".photo-page .media-card figcaption {")
    scoped=css[start:start+350]
    assert "width:100%" in scoped
    assert "text-align:center" in scoped
    assert "overflow:visible" in scoped


def test_pass6_preserves_successful_orientation_sizes_and_no_crop():
    css=pub.PRO_CSS
    assert "max-height:106mm !important" in css
    assert "max-height:91mm !important" in css
    assert "object-fit:contain !important" in css


def test_rc1_0_11_1_restores_explicit_original_file_links():
    source=__import__("inspect").getsource(pub)
    assert "Open original PDF" in source
    assert "Open original image" in source
