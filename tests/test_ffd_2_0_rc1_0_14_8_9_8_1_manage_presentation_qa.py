from pathlib import Path

UI=Path("src/reunion_companion/companion/beta_ui.py")

def _text():
    return UI.read_text()

def test_ryerson_crawler_control_has_spacing_from_status_text():
    text=_text()
    assert "action='/manage/ryerson/pause' style='margin-top:10px'" in text
    assert "action='/manage/ryerson/start' style='margin-top:10px'" in text

def test_recent_crawler_activity_has_spacing_before_first_result():
    text=_text()
    assert 'first_style=" style=\'margin-top:7px\'" if index==0 else ""' in text
    assert 'for index,item in enumerate(recent):' in text

def test_import_history_pager_matches_priorities_presentation():
    text=_text()
    assert "history_pager=\"<div class='rc-priority-pager'>\"" in text
    assert "pager.append(f\"<a class='button' href='/data?import_page={import_page-1}'>Previous</a>\")" in text
    assert "pager.append(f\"<a class='button' href='/data?import_page={import_page+1}'>Next</a>\")" in text
    assert "history_pager=\"<div class='publication-actions'" not in text
