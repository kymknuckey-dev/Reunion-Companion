from pathlib import Path

from reunion_companion.companion.media_reconciliation import media_filename_conforms


def test_media_filename_standard_accepts_identity_prefix_and_descriptive_text():
    assert media_filename_conforms('Knuckey, Mervyn Neil.jpg')
    assert media_filename_conforms('Knuckey, Mervyn Neil Wedding Photo.jpg')
    assert media_filename_conforms('Cox, Elaine Fay - Birth Certificate.pdf')
    assert media_filename_conforms("O'Connor-Smith, Mary Jane Portrait 1940.tif")


def test_media_filename_standard_rejects_nonconforming_prefixes():
    assert not media_filename_conforms('Mervyn Knuckey.jpg')
    assert not media_filename_conforms('IMG_4832.jpg')
    assert not media_filename_conforms('Knuckey Mervyn Neil.jpg')
    assert not media_filename_conforms('Knuckey,.jpg')
    assert not media_filename_conforms('1234, 5678.jpg')


def test_quality_page_places_filename_review_in_media_row_and_removes_redundant_cards():
    source=Path('src/reunion_companion/companion/beta_ui.py').read_text(encoding='utf-8')
    quality=source[source.index('def quality_page'):source.index('def quality_items_page')]
    assert "Non-standard filename · review" in quality
    assert "view=naming" in quality
    assert '("Missing media","missing_media"' not in quality
    assert '("Legacy PICT","legacy_pict"' not in quality
    assert '("Untitled sources","untitled_sources"' not in quality
    assert '("Place variants","place_variant_groups"' in quality
    assert '("Duplicate source titles","duplicate_source_titles"' in quality


def test_media_browser_exposes_naming_view_and_standard_copy():
    source=Path('src/reunion_companion/companion/beta_ui.py').read_text(encoding='utf-8')
    page=source[source.index('def media_reconciliation_page'):source.index('def timeline_tab')]
    assert "('naming','Non-standard filename · review','nonstandard_filenames')" in page
    assert "data['nonstandard_filenames']" in page
    assert 'Surname, First names' in page
