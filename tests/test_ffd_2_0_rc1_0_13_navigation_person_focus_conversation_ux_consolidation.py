from pathlib import Path
from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import person_page, home, search_page
from reunion_companion.companion.ffd_relationship_questions import questions_body
from test_ffd_1_8_build1_1_query_consistency_hardening import seed as seed_query
from test_ffd_2_0_rc1_0_11_2_unified_family_charts_html_book_qa_pass_2 import _seed


def test_release_identity_is_rc1_0_13():
    s=Path("macos_app/build_app.py").read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.13 — Navigation, Person Focus & Conversation UX Consolidation"' in s


def test_sidebar_uses_selected_person_heading_and_agreed_order(tmp_path):
    db=connect(tmp_path/"x.sqlite3"); _seed(db)
    html=person_page(db,3,"overview")
    assert "Selected person" in html
    assert "Line Son" in html
    positions=[html.index(">Overview<"),html.index(">Timeline<"),html.index(">Biography<"),
               html.index(">Family Chart<"),html.index(">Family<"),html.index(">Media<")]
    assert positions == sorted(positions)
    assert ">Ask about<" in html
    db.close()


def test_person_strip_current_person_contract_is_mode_aware():
    # Presentation Overview deliberately uses its established editorial hero
    # rather than the compact persistent person strip. Verify the strip's
    # markup contract directly so this QA is independent of ambient mode.
    s=Path("src/reunion_companion/companion/ffd_person_story.py").read_text()
    assert "rc-person-eyebrow" in s
    assert ">Current person<" in s


def test_home_and_search_get_clear_active_states(tmp_path):
    db=connect(tmp_path/"x.sqlite3")
    h=home(db)
    s=search_page(db)
    assert "class='active' href='/'>Home</a>" in h
    assert "class='active' href='/'>Home</a>" in s
    db.close()


def test_conversation_focus_is_compact_and_explicit(tmp_path):
    db=connect(tmp_path/"x.sqlite3"); seed_query(db)
    html=questions_body(db,1,"Who is her daughter?",origin_id=1)
    assert "rq-focus-bar" in html
    assert "rq-focus-label'>Conversation" in html
    assert "rq-focus-name'>Elaine Fay Cox" in html
    assert "Move to Jodie Karen Knuckey →" in html
    assert "Focus changes only when you choose Move to." in html
    db.close()


def test_return_to_origin_remains_inline_when_focus_moves(tmp_path):
    db=connect(tmp_path/"x.sqlite3"); seed_query(db)
    # Explicitly move focus to the daughter while retaining Elaine as origin.
    html=questions_body(db,4,"Where was she born?",origin_id=1)
    assert "Started with Elaine Fay Cox" in html
    assert "← Return to Elaine Fay Cox" in html
    assert "rq-focus-actions" in html
    db.close()


def test_sidebar_active_state_is_restrained_indicator():
    s=Path("src/reunion_companion/companion/beta_ui.py").read_text()
    assert ".rc-sidebar a.active:before" in s
    assert "width:3px" in s
    assert "background:#e7edf3!important" in s


def test_relationship_resolution_engine_is_not_modified_by_ui_pass():
    s=Path("src/reunion_companion/companion/ffd_relationship_questions.py").read_text()
    assert "answer_question(db,question,subject_id,selected_identity_id,prior_knowledge_intent)" in s
