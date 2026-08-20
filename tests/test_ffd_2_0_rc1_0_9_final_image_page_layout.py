from pathlib import Path

from reunion_companion.companion import publishing_v11 as pub


def test_final_photo_pair_group_is_shifted_down_without_changing_slot_geometry():
    css=pub.PRO_CSS
    start=css.index('.photo-page.photo-pair {')
    scoped=css[start:start+280]
    assert 'height:231mm' in scoped
    assert 'grid-template-rows:113mm 113mm' in scoped
    assert 'gap:5mm' in scoped
    assert 'transform:translateY(8mm)' in scoped


def test_final_image_sizes_and_no_crop_contract_remain_frozen():
    css=pub.PRO_CSS
    assert 'max-height:106mm !important' in css
    assert 'max-height:91mm !important' in css
    assert 'object-fit:contain !important' in css


def test_final_image_page_layout_specification_is_packaged():
    root=Path(__file__).resolve().parents[1]
    md=root/'docs/publishing/FFD-2.0-RC1.0.9-Image-Page-Layout-Specification.md'
    png=root/'docs/publishing/FFD-2.0-RC1.0.9-Image-Page-Layout-Specification.png'
    assert md.is_file()
    assert png.is_file()
    text=md.read_text()
    assert 'Two photographs per photograph page' in text
    assert '8 mm' in text
    assert 'must never be cropped' in text
