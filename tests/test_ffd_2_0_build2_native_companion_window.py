from pathlib import Path
import importlib.util,sys
MODULE=Path(__file__).parents[1]/"macos_app"/"build_app.py"; spec=importlib.util.spec_from_file_location("b2",MODULE); m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)
def test_identity(): assert int(m.APP_BUILD)>=2 and m.ENGINE_BASELINE=="FFD 1.9 RC1"
def test_webkit():
 s=m.swift_source(Path("/tmp/x")); assert "import WebKit" in s and "WKWebView" in s and "NSWorkspace.shared.open(companionURL)" not in s
def test_window():
 s=m.swift_source(Path("/tmp/x")); assert ".resizable" in s and "applicationShouldHandleReopen" in s and "windowShouldClose" in s
def test_external_links():
 s=m.swift_source(Path("/tmp/x")); assert "WKNavigationDelegate" in s and "NSWorkspace.shared.open(url)" in s
def test_lifecycle():
 s=m.swift_source(Path("/tmp/x")); assert ".venv/bin/python" in s and "p.terminate()" in s and "--no-browser" in s
def test_shell_identity():
 from reunion_companion import app_identity; assert app_identity.APP_SERIES=="2.0" and int(app_identity.APP_BUILD)>=2 and app_identity.ENGINE_BASELINE=="FFD 1.9 RC1"
