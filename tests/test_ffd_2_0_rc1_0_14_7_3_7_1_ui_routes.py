from pathlib import Path

def test_surname_bootstrap_ui_routes_exist():
    text=Path("src/reunion_companion/companion/beta_ui.py").read_text()
    post=text[text.index("def do_POST"):]
    assert '"/research/ryerson/targeted/start"' in post
    assert '"/research/ryerson/targeted/pause"' in post
    assert "start_targeted_bootstrap" in post
    assert "pause_targeted_bootstrap" in post

def test_surname_bootstrap_routes_remain_internal_after_unified_crawler_ui():
    text=Path("src/reunion_companion/companion/beta_ui.py").read_text()
    post=text[text.index("def do_POST"):]
    # RC1.0.14.8.9.7.1 deliberately removed the separate user-facing
    # Targeted Bootstrap forms.  The underlying POST routes remain available
    # because the unified Ryerson Crawler control coordinates both engines.
    assert '"/research/ryerson/targeted/start"' in post
    assert '"/research/ryerson/targeted/pause"' in post
    assert "action='/research/ryerson/targeted/start'" not in text
    assert "action='/research/ryerson/targeted/pause'" not in text
