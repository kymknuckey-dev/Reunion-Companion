from pathlib import Path

from reunion_companion.companion.database import connect
import reunion_companion.companion.beta_ui as ui
from reunion_companion.companion.ffd_home import home_body
from test_ffd_2_0_rc1_0_11_2_unified_family_charts_html_book_qa_pass_2 import _seed


def test_release_identity_is_rc1_0_13_1():
    s=Path("macos_app/build_app.py").read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.13.1 — Persistent Global Navigation, Person Header Parity & Home Explore Removal"' in s


def test_presentation_global_navigation_before_person_selection(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.sqlite3")
    monkeypatch.setattr(ui,"presentation_mode_enabled",lambda: True)
    html=ui.home(db)
    assert ">Home</a>" in html
    assert ">Search</a>" not in html
    assert ">Reports</a>" in html
    assert ">Priorities</a>" not in html
    assert ">Improve</a>" not in html
    assert ">Manage</a>" not in html
    db.close()


def test_research_global_navigation_before_person_selection(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.sqlite3")
    monkeypatch.setattr(ui,"presentation_mode_enabled",lambda: False)
    html=ui.home(db)
    assert ">Priorities</a>" in html
    assert ">Improve</a>" in html
    assert ">Manage</a>" in html
    assert ">Reports</a>" in html
    db.close()


def test_global_navigation_remains_when_person_selected(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.sqlite3"); _seed(db)
    monkeypatch.setattr(ui,"presentation_mode_enabled",lambda: False)
    html=ui.person_page(db,3,"overview")
    assert "Selected person" in html
    assert ">Priorities</a>" in html
    assert ">Improve</a>" in html
    assert ">Manage</a>" in html
    assert ">Publish</a>" in html
    assert ">Reports</a>" in html
    db.close()


def test_home_no_longer_renders_duplicate_explore_launch_cards(tmp_path):
    db=connect(tmp_path/"x.sqlite3")
    presentation=home_body(db,{},True)
    research=home_body(db,{},False)
    assert "<h2 class='ffd-section'>Explore</h2>" not in presentation
    assert "Find a Person" not in presentation
    assert "<h2 class='ffd-section'>Research</h2>" not in research
    assert "Research Priorities" not in research
    assert "Improve the Data" not in research
    assert "Data Manager" not in research
    assert "Family to Explore" not in presentation
    assert "Family History at a Glance" in research
    db.close()


def test_family_chart_has_same_person_header_as_other_person_pages(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.sqlite3"); _seed(db)
    monkeypatch.setattr(ui,"presentation_mode_enabled",lambda: False)
    html=ui.person_page(db,3,"family-chart")
    assert "rc-person-strip" in html
    assert ">Current person<" in html
    assert "Line Son" in html
    db.close()


def test_ask_about_has_person_header_and_separate_conversation_focus(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.sqlite3"); _seed(db)
    monkeypatch.setattr(ui,"presentation_mode_enabled",lambda: False)
    html=ui.render_get(db,"/questions",{"person":"3","origin":"3"})
    assert "rc-person-strip" in html
    assert ">Current person<" in html
    assert "Line Son" in html
    assert "rq-focus-bar" in html
    assert "rq-focus-label'>Conversation" in html
    db.close()


def test_global_destination_active_state_contract():
    s=Path("src/reunion_companion/companion/beta_ui.py").read_text()
    assert 'active="priorities"' in s
    assert 'active="improve"' in s
    assert 'active="manage"' in s
    assert '"reports")' in s
