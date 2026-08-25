from types import SimpleNamespace

from reunion_companion.companion.ryerson_safari_transport import _safari_do_javascript
from reunion_companion.companion.ryerson_safari_harvest import _pagination_javascript

def completed(stdout="",stderr="",returncode=0):
    return SimpleNamespace(stdout=stdout,stderr=stderr,returncode=returncode)

def test_javascript_is_passed_as_argv_not_embedded():
    seen={}
    def runner(args,**kwargs):
        seen["args"]=args
        return completed(stdout="ok\n")
    js='(() => { const x="quoted"; return /[>»]+/.test(x); })()'
    result=_safari_do_javascript(js,runner=runner)
    assert result=="ok"
    args=seen["args"]
    assert args[0]=="osascript"
    assert args[-1]==js
    script_parts=[args[i+1] for i,x in enumerate(args[:-1]) if x=="-e"]
    assert all(js not in part for part in script_parts)

def test_real_pagination_script_passed_unchanged():
    seen={}
    def runner(args,**kwargs):
        seen["args"]=args
        return completed(stdout='{"current":"x","links":[]}\n')
    js=_pagination_javascript()
    result=_safari_do_javascript(js,runner=runner)
    assert result.startswith('{"current"')
    assert seen["args"][-1]==js
    assert "»" in js
