from pathlib import Path

def test_surname_bootstrap_ui_routes_exist():
    text=Path("src/reunion_companion/companion/beta_ui.py").read_text()
    post=text[text.index("def do_POST"):]
    assert '"/research/ryerson/surnames/start"' in post
    assert '"/research/ryerson/surnames/pause"' in post
    assert "start_bootstrap" in post
    assert "pause_bootstrap" in post

def test_surname_bootstrap_forms_match_post_routes():
    text=Path("src/reunion_companion/companion/beta_ui.py").read_text()
    assert "action='/research/ryerson/surnames/start'" in text
    assert "action='/research/ryerson/surnames/pause'" in text
