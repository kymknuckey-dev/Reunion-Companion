from reunion_companion.companion import publishing_v11 as pub

def test_photo_pages_are_explicit_not_free_flow():
    assert ".photo-grid { display:block; }" in pub.PRO_CSS
    assert ".photo-page.photo-pair" in pub.PRO_CSS
    assert "break-after:page" in pub.PRO_CSS

def test_photo_pair_is_maximum_two():
    import inspect
    s=inspect.getsource(pub._person_section)
    assert "pair=photos[i:i+2]" in s
    assert "range(0,len(photos),2)" in s

def test_portrait_uses_shared_two_slot_photo_page():
    import inspect
    s=inspect.getsource(pub._person_section)
    assert "photo-page photo-pair" in s
    assert "single-photo" not in s

def test_html_uses_same_publication_units():
    assert "@media screen" in pub.PRO_CSS
    assert ".photo-page.photo-pair" in pub.PRO_CSS

def test_rc_identity():
    from reunion_companion import app_identity
    assert app_identity.APP_RELEASE_DISPLAY=="FFD 2.0 RC1.0.3"
    assert app_identity.APP_RELEASE_NAME=="Birth Document Fitted Page Structural Repair"
    assert app_identity.ENGINE_BASELINE=="FFD 1.9 RC1"
