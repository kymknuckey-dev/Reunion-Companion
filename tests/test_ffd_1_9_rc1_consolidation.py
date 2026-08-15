from reunion_companion.companion.version_identity import (
    FFD_SERIES, FFD_BUILD, RELEASE_NAME, RELEASE_TAG, FFD_DISPLAY,
)
from reunion_companion.companion.person_narrative import NARRATIVE_VERSION


def test_rc1_release_identity():
    assert FFD_SERIES == "1.9"
    assert FFD_BUILD == "RC1"
    assert RELEASE_NAME == "Consolidation Release Candidate"
    assert RELEASE_TAG == "ffd-1.9-rc1"
    assert FFD_DISPLAY == "FFD 1.9 RC1"


def test_rc1_freezes_build_4_0_1_biography_contract():
    # RC1 is consolidation, not a new biography implementation. Keeping the
    # Build 4.0.1 narrative version also avoids needless cache regeneration.
    assert NARRATIVE_VERSION == "ffd-1.9-build-4.0.1-v1"
