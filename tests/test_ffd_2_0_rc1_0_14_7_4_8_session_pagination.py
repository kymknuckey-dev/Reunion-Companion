from reunion_companion.companion import ryerson_surname_bootstrap as mod

def test_historical_cache_keys_do_not_drive_current_run_repeat_detection():
    historical={"page1-a","page2-a"}
    session_seen=set()
    page1={"page1-a"}
    page2={"page2-a"}
    assert mod._page_is_new_for_session(page1,session_seen)
    session_seen.update(page1)
    assert "page2-a" in historical
    assert mod._page_is_new_for_session(page2,session_seen)

def test_exact_current_session_repeat_is_rejected():
    session_seen={"page1-a","page1-b"}
    repeated={"page1-a","page1-b"}
    assert not mod._page_is_new_for_session(repeated,session_seen)

def test_partially_new_page_is_accepted():
    session_seen={"a","b"}
    page={"b","c"}
    assert mod._page_is_new_for_session(page,session_seen)
