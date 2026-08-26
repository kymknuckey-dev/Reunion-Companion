from reunion_companion.companion.ryerson_safari_harvest import pagination_links
from reunion_companion.companion.ryerson_surname_bootstrap import _select_forward_pagination_link


def test_shared_hash_pager_controls_are_not_collapsed(monkeypatch):
    import reunion_companion.companion.ryerson_safari_harvest as mod
    payload='''{"current":"https://ryersonindex.org/search.php?page=1","links":[
      {"text":"2","href":"https://ryersonindex.org/search.php#"},
      {"text":"3","href":"https://ryersonindex.org/search.php#"},
      {"text":"4","href":"https://ryersonindex.org/search.php#"},
      {"text":"5","href":"https://ryersonindex.org/search.php#"},
      {"text":"6","href":"https://ryersonindex.org/search.php#"},
      {"text":"7","href":"https://ryersonindex.org/search.php#"},
      {"text":"Next»","href":"https://ryersonindex.org/search.php#"},
      {"text":"2","href":"https://ryersonindex.org/search.php#"},
      {"text":"3","href":"https://ryersonindex.org/search.php#"},
      {"text":"Next»","href":"https://ryersonindex.org/search.php#"}
    ]}'''
    monkeypatch.setattr(mod,"_safari_do_javascript",lambda js:payload)
    links=pagination_links()
    assert [x["text"] for x in links]==["2","3","4","5","6","7","Next»"]


def test_forward_selector_uses_next_numeric_control():
    links=[
        {"text":"«Previous","href":"https://ryersonindex.org/search.php#"},
        {"text":"2","href":"https://ryersonindex.org/search.php#"},
        {"text":"3","href":"https://ryersonindex.org/search.php#"},
        {"text":"4","href":"https://ryersonindex.org/search.php#"},
        {"text":"Next»","href":"https://ryersonindex.org/search.php#"},
    ]
    assert _select_forward_pagination_link(links,2)==(3,"https://ryersonindex.org/search.php#")


def test_forward_selector_uses_next_when_visible_numeric_window_ends():
    links=[
        {"text":"«Previous","href":"https://ryersonindex.org/search.php#"},
        {"text":"2","href":"https://ryersonindex.org/search.php#"},
        {"text":"3","href":"https://ryersonindex.org/search.php#"},
        {"text":"4","href":"https://ryersonindex.org/search.php#"},
        {"text":"5","href":"https://ryersonindex.org/search.php#"},
        {"text":"6","href":"https://ryersonindex.org/search.php#"},
        {"text":"7","href":"https://ryersonindex.org/search.php#"},
        {"text":"Next»","href":"https://ryersonindex.org/search.php#"},
    ]
    assert _select_forward_pagination_link(links,7)==(8,"https://ryersonindex.org/search.php#")


def test_no_forward_control_means_final_page():
    links=[
        {"text":"«Previous","href":"https://ryersonindex.org/search.php#"},
        {"text":"5","href":"https://ryersonindex.org/search.php#"},
        {"text":"6","href":"https://ryersonindex.org/search.php#"},
        {"text":"7","href":"https://ryersonindex.org/search.php#"},
    ]
    assert _select_forward_pagination_link(links,7) is None
