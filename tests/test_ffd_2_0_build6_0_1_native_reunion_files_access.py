from pathlib import Path
import importlib.util,sys
MODULE=Path(__file__).parents[1]/"macos_app"/"build_app.py"
spec=importlib.util.spec_from_file_location("b601",MODULE); m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)

def test_identity():
    assert m.APP_BUILD=="6"
    assert m.APP_RELEASE.startswith("FFD 2.0 ")
    assert m.ENGINE_BASELINE=="FFD 1.9 RC1"

def test_native_folder_grant_and_persistent_security_scope():
    s=m.swift_source(Path("/tmp/x"))
    assert 'Reunion Files Access…' in s
    assert 'NSOpenPanel()' in s
    assert 'canChooseDirectories=true' in s
    assert '.withSecurityScope' in s
    assert 'startAccessingSecurityScopedResource()' in s
    assert 'stopAccessingSecurityScopedResource()' in s
    assert 'reunion-files.bookmark' in s
    assert 'restoreReunionFilesAccess()' in s

def test_diagnostics_exposes_granted_folder():
    s=m.swift_source(Path("/tmp/x"))
    assert 'Reunion Files: \\(reunionFilesDisplay)' in s

def test_media_permission_failure_is_graceful():
    src=(Path(__file__).parents[1]/"src/reunion_companion/companion/beta_ui.py").read_text()
    assert 'except PermissionError:' in src
    assert 'send_error(403,"Reunion media folder access has not been granted")' in src
