from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_rc105_assets_are_present():
    assert (ROOT/'macos_app/assets/AppIconMaster.png').is_file()
    for name in ('AppIcon.png','HeaderMark.png','PublishingMark.png','InAppBrand.png'):
        assert (ROOT/'src/reunion_companion/companion/branding_assets'/name).is_file()


def test_rc105_mac_builder_generates_native_icon_without_changing_install_shape():
    text=(ROOT/'macos_app/build_app.py').read_text()
    assert 'CFBundleIconFile":"ReunionCompanion.icns"' in text
    assert 'def build_app_icon' in text
    assert '--collect-data","reunion_companion"' in text
    assert 'Runtime/ReunionCompanionBackend' in text


def test_rc105_companion_brand_survives_navigation_redesign():
    text=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    assert 'header_brand_html()' in text
    assert 'rc-header-mark' in text


def test_rc105_home_and_publication_identity_are_integrated():
    home=(ROOT/'src/reunion_companion/companion/ffd_home.py').read_text()
    pub=(ROOT/'src/reunion_companion/companion/publishing_v11.py').read_text()
    brand=(ROOT/'src/reunion_companion/companion/branding.py').read_text()
    assert 'home_brand_html()' in home
    assert 'publishing_mark_uri()' in pub
    assert 'Your family history. Together.' in brand

def test_visual_qa_pass1_assets_use_the_canvas_effectively():
    from PIL import Image
    checks = [
        (ROOT/'macos_app/assets/AppIconMaster.png', 0.88),
        (ROOT/'src/reunion_companion/companion/branding_assets/HeaderMark.png', 0.84),
        (ROOT/'src/reunion_companion/companion/branding_assets/PublishingMark.png', 0.84),
    ]
    for path, minimum in checks:
        im=Image.open(path).convert('RGBA')
        bbox=im.getchannel('A').getbbox()
        assert bbox is not None
        fill=max((bbox[2]-bbox[0])/im.width,(bbox[3]-bbox[1])/im.height)
        assert fill >= minimum, (path, fill)


def test_visual_qa_pass1_display_sizes_and_bundle_build():
    ui=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    pub=(ROOT/'src/reunion_companion/companion/publishing_v11.py').read_text()
    build=(ROOT/'macos_app/build_app.py').read_text()
    package=(ROOT/'macos_app/package_dmg.py').read_text()
    assert '.rc-header-mark{width:46px;height:46px;' in ui
    assert '.publishing-mark { width:38mm; height:38mm;' in pub
    assert 'APP_BUILD="6"' in build
    assert 'APP_BUILD="6"' in package
    assert 'Visual QA Pass 2' in build


def test_visual_qa_pass2_tightens_native_icon_and_verifies_bundle_icon():
    from PIL import Image
    master=Image.open(ROOT/'macos_app/assets/AppIconMaster.png').convert('RGBA')
    bbox=master.getchannel('A').getbbox()
    assert bbox is not None
    fill=max((bbox[2]-bbox[0])/master.width,(bbox[3]-bbox[1])/master.height)
    assert fill >= 0.97, fill
    build=(ROOT/'macos_app/build_app.py').read_text()
    package=(ROOT/'macos_app/package_dmg.py').read_text()
    assert 'CFBundleIconName":"ReunionCompanion"' in build
    assert 'macOS application icon was not produced correctly' in build
    assert "Built application does not declare ReunionCompanion.icns" in package
    assert 'Visual QA Pass 2' in build
    assert 'Visual QA Pass 2' in package
