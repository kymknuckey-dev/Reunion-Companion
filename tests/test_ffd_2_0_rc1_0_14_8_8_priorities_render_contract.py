import inspect

from reunion_companion.companion.beta_ui import research_page


def test_research_priorities_render_does_not_materialise_external_discoveries():
    """Opening Priorities is a read/render operation, not a genealogy-wide discovery scan."""
    source = inspect.getsource(research_page)
    assert "materialize_existing_ryerson_discoveries(db)" not in source
    assert "materialize_person_level_ryerson_findings(db)" not in source
