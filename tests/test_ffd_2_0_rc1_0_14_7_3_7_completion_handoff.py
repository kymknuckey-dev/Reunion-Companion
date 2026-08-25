from reunion_companion.companion.ryerson_surname_bootstrap import _select_forward_pagination_link

def test_page_two_does_not_go_back_to_page_one():
    links=[
        {"text":"1","href":"https://ryersonindex.org/search.php?page=1"},
        {"text":"2","href":"https://ryersonindex.org/search.php?page=2"},
    ]
    assert _select_forward_pagination_link(links,2) is None

def test_page_one_selects_page_two():
    links=[
        {"text":"1","href":"https://ryersonindex.org/search.php?page=1"},
        {"text":"2","href":"https://ryersonindex.org/search.php?page=2"},
    ]
    assert _select_forward_pagination_link(links,1)==(
        2,"https://ryersonindex.org/search.php?page=2"
    )

def test_forward_selection_chooses_smallest_later_page():
    links=[
        {"text":"3","href":"https://ryersonindex.org/search.php?page=3"},
        {"text":"2","href":"https://ryersonindex.org/search.php?page=2"},
        {"text":"1","href":"https://ryersonindex.org/search.php?page=1"},
    ]
    assert _select_forward_pagination_link(links,1)[0]==2

def test_visited_forward_link_is_skipped():
    page2="https://ryersonindex.org/search.php?page=2"
    links=[
        {"text":"2","href":page2},
        {"text":"3","href":"https://ryersonindex.org/search.php?page=3"},
    ]
    assert _select_forward_pagination_link(links,1,visited={page2})[0]==3
