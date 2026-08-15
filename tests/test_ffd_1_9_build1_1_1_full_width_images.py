from reunion_companion.companion.publishing_v11 import PRO_CSS
from reunion_companion.companion.beta_ui import person_page
from reunion_companion.companion.database import connect
from reunion_companion.companion.version_identity import FFD_DISPLAY, RELEASE_TAG


def test_all_publication_image_shapes_use_natural_size_capped_at_content_width():
    assert ".media-card.media-landscape img," in PRO_CSS
    assert ".media-card.media-portrait img," in PRO_CSS
    assert ".media-card.media-square img," in PRO_CSS
    assert ".media-card.hero img {" in PRO_CSS
    block=PRO_CSS.split(".media-card.media-landscape img,",1)[1].split("}",1)[0]
    assert "width:auto;" in block
    assert "max-width:100%;" in block
    assert "height:auto;" in block
    assert "max-height:none;" in block


def test_activity_spinner_retained_without_final_explanatory_line(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    db.execute("INSERT INTO people(id,display_name,sex) VALUES(1,'Example Person','M')"); db.commit()
    html=person_page(db,1,'publish')
    assert 'rc-spinner' in html
    assert 'Preparing family information' in html
    assert 'Writing publication narrative' in html
    assert 'Rendering the document and media' in html
    assert 'These stages may overlap' not in html
    assert 'no artificial percentage' not in html


def test_release_identity_is_build_1_1_1():
    assert FFD_DISPLAY.startswith('FFD 1.9 ')
    assert RELEASE_TAG.startswith('ffd-1.9-')
