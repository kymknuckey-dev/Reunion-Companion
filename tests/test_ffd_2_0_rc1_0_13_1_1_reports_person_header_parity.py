from reunion_companion.companion.database import connect
import reunion_companion.companion.beta_ui as ui
from test_ffd_2_0_rc1_0_11_2_unified_family_charts_html_book_qa_pass_2 import _seed


def test_contextual_reports_has_person_header_in_research_mode(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.sqlite3"); _seed(db)
    monkeypatch.setattr(ui,"presentation_mode_enabled",lambda: False)
    html=ui.publishing_page(db,origin_pid=3)
    assert "rc-person-strip" in html
    assert ">Current person<" in html
    assert "Line Son" in html
    assert "← Back to Line Son" not in html
    assert "class='active' href='/reports?origin=3'>Reports</a>" in html
    db.close()


def test_contextual_reports_has_person_header_in_presentation_mode(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.sqlite3"); _seed(db)
    monkeypatch.setattr(ui,"presentation_mode_enabled",lambda: True)
    html=ui.publishing_page(db,origin_pid=3)
    assert "rc-person-strip" in html
    assert ">Current person<" in html
    assert "Line Son" in html
    assert "← Back to Line Son" not in html
    db.close()


def test_global_reports_remains_person_neutral(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.sqlite3"); _seed(db)
    monkeypatch.setattr(ui,"presentation_mode_enabled",lambda: False)
    html=ui.publishing_page(db)
    assert "<section class='rc-person-strip'>" not in html
    assert ">Current person<" not in html
    assert "← Back to" not in html
    assert "class='active' href='/reports'>Reports</a>" in html
    db.close()


def test_reports_parity_does_not_change_report_actions():
    s=open("src/reunion_companion/companion/beta_ui.py").read()
    assert "action='/publication/open'" in s
    assert "action='/publication/delete'" in s
    assert "action='/publication/remove'" in s
