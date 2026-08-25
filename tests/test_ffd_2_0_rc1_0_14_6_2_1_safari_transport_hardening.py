from types import SimpleNamespace
from reunion_companion.companion.ryerson_safari_transport import _ryerson_page_is_busy,_safari_open

def completed(stdout="",stderr="",returncode=0):
    return SimpleNamespace(stdout=stdout,stderr=stderr,returncode=returncode)

def test_exact_live_server_overloaded_page_is_busy():
    html="<h1>Server Overloaded</h1><p>Sorry, our server is feeling a bit overworked and is unable to handle the number of requests at this time.</p>"
    assert _ryerson_page_is_busy(html)

def test_existing_busy_language_still_recognised():
    assert _ryerson_page_is_busy("<p>Server is busy. Please try again later.</p>")

def test_normal_page_not_busy():
    assert not _ryerson_page_is_busy("<html><body><form><input name='surname'></form></body></html>")

def test_safari_open_uses_fresh_get_navigation_not_reload():
    seen={}
    def runner(args,**kwargs):
        seen["script"]=args[-1]
        return completed()
    _safari_open("https://ryersonindex.org/search.php",runner=runner)
    script=seen["script"].lower()
    assert "set url of front document" in script
    assert "reload" not in script
    assert "history.go" not in script
