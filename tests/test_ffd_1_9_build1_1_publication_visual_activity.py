from pathlib import Path
from PIL import Image
from reunion_companion.companion.database import connect
from reunion_companion.companion.publishing_v11 import _image_block, PRO_CSS
from reunion_companion.companion.beta_ui import person_page
from reunion_companion.companion.version_identity import FFD_DISPLAY, RELEASE_TAG


def _media(path, mid=1):
    return {"id":mid,"file_path":str(path),"title":path.stem,"exists_on_disk":1}


def test_publication_removes_cards_and_uses_orientation_rules(tmp_path):
    landscape=tmp_path/'landscape.jpg'; portrait=tmp_path/'portrait.jpg'; square=tmp_path/'square.jpg'
    Image.new('RGB',(1200,700)).save(landscape)
    Image.new('RGB',(700,1200)).save(portrait)
    Image.new('RGB',(900,900)).save(square)
    assert "media-landscape" in _image_block(_media(landscape), output_html=tmp_path/'book.html')
    assert "media-portrait" in _image_block(_media(portrait,2), output_html=tmp_path/'book.html')
    assert "media-square" in _image_block(_media(square,3), output_html=tmp_path/'book.html')
    assert ".media-card {\n  border:0;" in PRO_CSS
    assert ".person-summary { border:0;" in PRO_CSS
    assert ".media-card.media-landscape img," in PRO_CSS
    assert ".media-card.media-portrait img," in PRO_CSS
    assert ".media-card.hero img {" in PRO_CSS
    assert "max-width:100%;" in PRO_CSS
    assert "max-height:none;" in PRO_CSS


def test_small_landscape_is_not_forced_to_full_width(tmp_path):
    p=tmp_path/'small.jpg'; Image.new('RGB',(500,300)).save(p)
    html=_image_block(_media(p), output_html=tmp_path/'book.html')
    assert "media-landscape" in html and "media-small" in html
    assert "width:auto;" in PRO_CSS and "max-width:100%;" in PRO_CSS


def test_publish_page_has_animated_activity_feedback(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    db.execute("INSERT INTO people(id,display_name,sex) VALUES(1,'Example Person','M')"); db.commit()
    html=person_page(db,1,'publish')
    assert "rc-spinner" in html
    assert "@keyframes rc-spin" in html
    assert "Preparing family information" in html
    assert "Writing publication narrative" in html
    assert "Rendering the document and media" in html
    assert "no artificial percentage" not in html


def test_release_identity_is_ffd_1_9_build_1_1_1():
    assert FFD_DISPLAY=='FFD 1.9 Build 1.1.1'
    assert RELEASE_TAG=='ffd-1.9-build-1.1.1'
