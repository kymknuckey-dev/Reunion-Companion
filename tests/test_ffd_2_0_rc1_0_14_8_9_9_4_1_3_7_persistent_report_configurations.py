from pathlib import Path
import re

import pytest

from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import book_scope_page, descendant_report_page
from reunion_companion.companion.report_configurations import (
    delete_report_configuration,
    get_report_configuration,
    list_report_configurations,
    save_report_configuration,
)
from test_ffd_2_0_rc1_0_11_2_unified_family_charts_html_book_qa_pass_2 import _seed


def test_multiple_named_family_history_configurations_persist_across_reopen(tmp_path):
    path = tmp_path / "x.sqlite3"
    db = connect(path)
    first = save_report_configuration(
        db,
        "family_history",
        3,
        "Dad's Printed History",
        {"endpoint": 1, "selected_family_ids": [101, 102], "format": "PDF"},
    )
    second = save_report_configuration(
        db,
        "family_history",
        3,
        "Web Family History",
        {"endpoint": 1, "selected_family_ids": [101], "format": "HTML"},
    )
    assert first != second
    db.close()

    db = connect(path)
    configs = list_report_configurations(db, "family_history", 3)
    assert [c["name"] for c in configs] == ["Dad's Printed History", "Web Family History"]
    assert configs[0]["settings"]["format"] == "PDF"
    assert configs[1]["settings"]["format"] == "HTML"
    db.close()


def test_duplicate_name_is_not_silently_overwritten_and_loaded_config_can_be_updated(tmp_path):
    db = connect(tmp_path / "x.sqlite3")
    cid = save_report_configuration(db, "family_history", 3, "Full History", {"endpoint": 1})
    with pytest.raises(ValueError, match="already exists"):
        save_report_configuration(db, "family_history", 3, "Full History", {"endpoint": 2})
    save_report_configuration(
        db,
        "family_history",
        3,
        "Full History",
        {"endpoint": 2, "format": "HTML"},
        config_id=cid,
    )
    assert get_report_configuration(db, cid)["settings"]["endpoint"] == 2
    assert get_report_configuration(db, cid)["settings"]["format"] == "HTML"
    db.close()


def test_family_history_configuration_restores_endpoint_family_choices_and_saved_format(tmp_path):
    db = connect(tmp_path / "x.sqlite3")
    _seed(db)
    cid = save_report_configuration(
        db,
        "family_history",
        1,
        "Short Web History",
        {"endpoint": 6, "selected_family_ids": [101], "format": "HTML"},
    )
    html = book_scope_page(db, 1, {"config": str(cid)})
    assert "Saved Report Configurations" in html
    assert "Short Web History" in html
    assert "Saved output: HTML" in html
    assert "<option value='6' selected>" in html
    assert not re.search(r"name='family_100' value='1' checked", html)
    assert re.search(r"name='family_101' value='1' checked", html)
    assert "Create Print-ready PDF" in html
    assert "Create HTML" in html
    db.close()


def test_descendant_configuration_restores_family_and_generations_without_changing_publish_actions(tmp_path):
    db = connect(tmp_path / "x.sqlite3")
    _seed(db)
    cid = save_report_configuration(
        db,
        "descendant_report",
        3,
        "Four Generation PDF",
        {"family_id": 101, "generations": 4, "format": "PDF"},
    )
    html = descendant_report_page(db, 3, {"config": str(cid)})
    assert "Four Generation PDF" in html
    assert "Saved output: PDF" in html
    assert "type='hidden' name='family_id' value='101'" in html
    assert "<option value='4' selected>4 generations</option>" in html
    assert "Create Print-ready PDF" in html
    assert "Create HTML" in html
    db.close()


def test_delete_removes_only_named_configuration(tmp_path):
    db = connect(tmp_path / "x.sqlite3")
    a = save_report_configuration(db, "family_history", 3, "A", {"endpoint": 1})
    b = save_report_configuration(db, "family_history", 3, "B", {"endpoint": 2})
    assert delete_report_configuration(db, a, report_type="family_history", start_person_id=3)
    assert get_report_configuration(db, a) is None
    assert get_report_configuration(db, b)["name"] == "B"
    db.close()


def test_configuration_save_does_not_use_publish_progress_path():
    source = Path("src/reunion_companion/companion/beta_ui.py").read_text()
    assert "if(s&&s.name==='format')" in source
    assert "/report-config/family-history/" in source
    assert "/report-config/descendant/" in source
