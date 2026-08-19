from pathlib import Path
from reunion_companion.companion import person_narrative

ROOT=Path(__file__).resolve().parents[1]
PUB=(ROOT/'src/reunion_companion/companion/publishing_v11.py').read_text()
MODEL=(ROOT/'src/reunion_companion/companion/family_publication_model.py').read_text()
BUILD=(ROOT/'macos_app/build_app.py').read_text()


def test_release_identity():
    assert 'APP_RELEASE="FFD 2.0 RC1.0.9 — Media Semantics & Book Presentation Pass 6"' in BUILD


def test_death_other_and_marriage_pdf_sections_use_birth_model_fitted_page():
    assert 'def _fitted_document_block' in PUB
    assert "class='document-fitted-page" in PUB
    assert '_fitted_document_block(first,output_html,label' in PUB
    assert '_fitted_document_block(m,output_html,"Marriage Documents"' in PUB
    assert '.document-fitted-page { display:none; break-before:page;' in PUB


def test_image_marriage_certificates_are_family_marriage_documents():
    assert 'family_attached_document=' in MODEL
    assert 'kind in ("document","document-image","marriage-document")' in MODEL
    assert '("marriage","wedding")' in MODEL


def test_book_generates_missing_canonical_biography():
    assert 'person_narrative(db,pid,force=True)' in PUB
    assert '_publication_biography(db,pid)' in PUB


def test_changed_metadata_is_excluded_from_narrative_evidence():
    source=Path(person_narrative.__file__).read_text()
    assert "typ.casefold() in ('changed','change')" in source
    assert "(r[5] or '').upper()=='CHAN'" in source


def test_facts_only_biography_is_deterministic_not_llm_invented_change_prose():
    source=Path(person_narrative.__file__).read_text()
    assert 'def _deterministic_fact_narrative' in source
    assert 'if not evidence and fact_text:' in source
    assert '_deterministic_fact_narrative(p,facts,families)' in source


def test_book_individual_overview_uses_compact_family_history_structure():
    assert "Life &amp; Biography" in PUB
    assert 'person-summary-grid' in PUB
    for label in ('Birth Date','Birth Place','Occupation','Education','Religion','Father','Mother','Spouse','Marriage Date','Marriage Place','Children'):
        assert label in PUB


def test_incoming_spouse_context_is_deferred_not_implemented():
    # Pass 1 records the design separately; it must not alter traversal yet.
    assert 'Incoming Spouse Family Context' not in PUB
