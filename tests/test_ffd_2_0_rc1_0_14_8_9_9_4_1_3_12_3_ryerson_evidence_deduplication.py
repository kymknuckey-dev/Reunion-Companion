from pathlib import Path

from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence import add_external_evidence, external_evidence_for_person


def _bickle(db, *, event_type, event_date, publication_date, confidence):
    return add_external_evidence(
        db,
        person_gedcom_xref="@I4798@",
        person_name_snapshot="John Stanley Herbert Bickle",
        source_name="Ryerson",
        evidence_type="death_notice",
        source_record_name="John Stanley Herbert (Jack) BICKLE",
        event_type=event_type,
        event_date=event_date,
        publication="Adelaide Advertiser",
        publication_date=publication_date,
        match_confidence=confidence,
        review_status="new",
    )


def test_bickle_rediscovery_returns_existing_finding_instead_of_inserting_duplicate(tmp_path):
    db=connect(tmp_path / "bickle.sqlite3")
    first=_bickle(db,event_type="Death",event_date="20JUL2012",publication_date="24JUL2012",confidence=95)
    second=_bickle(db,event_type="Death",event_date="20JUL2012",publication_date="24JUL2012",confidence=95)
    rows=external_evidence_for_person(db,"@I4798@")
    assert second == first
    assert len(rows) == 1
    assert rows[0]["source_record_name"] == "John Stanley Herbert (Jack) BICKLE"


def test_distinct_bickle_publication_dates_remain_distinct_findings(tmp_path):
    db=connect(tmp_path / "bickle.sqlite3")
    first=_bickle(db,event_type="Publication",event_date="25JUL2012",publication_date="25JUL2012",confidence=55)
    second=_bickle(db,event_type="Publication",event_date="26JUL2012",publication_date="26JUL2012",confidence=75)
    assert first != second
    assert len(external_evidence_for_person(db,"@I4798@")) == 2


def test_release_identity_ryerson_evidence_deduplication():
    expected="FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.3 — Ryerson Evidence Deduplication"
    assert f'APP_RELEASE="{expected}"' in Path("macos_app/build_app.py").read_text()
    assert f'APP_RELEASE="{expected}"' in Path("macos_app/package_dmg.py").read_text()
