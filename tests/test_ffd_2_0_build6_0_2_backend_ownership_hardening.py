from pathlib import Path
import importlib.util,sys,json
ROOT=Path(__file__).parents[1]
MODULE=ROOT/'macos_app/build_app.py'
spec=importlib.util.spec_from_file_location('b602',MODULE); m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)

def test_identity():
    assert m.APP_BUILD=='6'
    assert m.APP_RELEASE.startswith('FFD 2.0 ')
    assert m.ENGINE_BASELINE=='FFD 1.9 RC1'

def test_launcher_requires_backend_identity_before_attach():
    s=m.swift_source(Path('/tmp/x'))
    assert '/runtime/identity' in s
    assert 'reunion-companion-backend' in s
    assert 'identity["protocol"] as? Int == 1' in s
    assert 'identity["application"] as? String == "FFD 2.0 RC1.0.3"' in s
    assert 'identity["engine_baseline"] as? String == "FFD 1.9 RC1"' in s
    assert 'if self.isCompanionReady()' in s

def test_foreign_or_stale_port_owner_is_rejected_not_killed():
    s=m.swift_source(Path('/tmp/x'))
    assert 'if self.port8765Occupied()' in s
    assert 'will not attach to it' in s
    assert 'Quit the older Reunion Companion or other service using port 8765' in s
    # Termination remains limited to the Process object this launcher created.
    assert 'if let p=backend,p.isRunning { p.terminate()' in s
    assert 'pkill' not in s and 'kill(' not in s

def test_backend_exposes_runtime_identity_endpoint():
    src=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    assert 'u.path=="/runtime/identity"' in src
    assert '"service":"reunion-companion-backend"' in src
    assert '"protocol":1' in src
    assert 'APP_DISPLAY' in src and 'ENGINE_BASELINE' in src

def test_authoritative_shell_identity():
    from reunion_companion import app_identity
    assert app_identity.APP_DISPLAY.startswith('FFD 2.0 ')
    assert app_identity.APP_RELEASE_DISPLAY.startswith('FFD 2.0 ')
    assert app_identity.APP_RELEASE_NAME
    assert app_identity.ENGINE_BASELINE=='FFD 1.9 RC1'
