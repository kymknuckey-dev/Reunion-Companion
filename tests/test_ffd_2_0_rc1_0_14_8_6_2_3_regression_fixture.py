from pathlib import Path


def test_research_regression_fixture_materialises_incomplete_death():
    text=Path("tests/test_ffd_2_0_rc1_0_14_8_5_1_research_regression.py").read_text()
    assert "Incomplete Person" in text
    assert "INSERT INTO events" in text
    assert "VALUES(2,'Death',NULL,NULL,'note')" in text
    assert 'assert "Death details incomplete" in html' in text
