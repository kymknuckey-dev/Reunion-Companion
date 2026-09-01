from pathlib import Path


def test_family_history_typography_is_gently_tightened():
    src = Path('src/reunion_companion/companion/publishing_v11.py').read_text()
    assert 'font-size:10pt; line-height:1.36' in src
    assert 'h1 { font-size:22pt;' in src
    assert 'h2 { font-size:14pt; margin:5.5mm 0 2.5mm;' in src
    assert 'h3 { font-size:11pt; margin:3.2mm 0 1.2mm;' in src
    # Keep the established A4 page geometry unchanged in this pass.
    assert 'margin:16mm 15mm 18mm 15mm;' in src


def test_redundant_children_section_and_forced_page_break_are_removed():
    src = Path('src/reunion_companion/companion/publishing_v11.py').read_text()
    assert "<div class='pagebreak'></div><h2>Children</h2>" not in src
    assert 'No children are recorded for this family.' not in src
    # Descendant/family chart generation remains present after person profiles.
    assert "P.append(\"<div class='family-chart-pair'>\")" in src


def test_legacy_family_history_path_matches_page_economy_policy():
    src = Path('src/reunion_companion/companion/publishing_v10.py').read_text()
    assert 'font-size:10pt; line-height:1.36' in src
    assert 'h1 { font-size:22pt;' in src
    assert 'h2 { font-size:14pt;' in src
    assert 'h3 { font-size:11pt;' in src
    assert "<h2>Children</h2>" not in src
    assert '@page { size:A4; margin:16mm 15mm 18mm 15mm; }' in src


def test_repeated_chapter_source_sections_are_removed_but_source_index_support_remains():
    v11 = Path('src/reunion_companion/companion/publishing_v11.py').read_text()
    v10 = Path('src/reunion_companion/companion/publishing_v10.py').read_text()
    assert 'Sources Used in This Chapter' not in v11
    assert 'Sources Used in This Chapter' not in v10
    # The consolidated book-level source index remains part of publishing_v11.
    assert 'Source Index' in v11
    assert 'source_label' in v11
