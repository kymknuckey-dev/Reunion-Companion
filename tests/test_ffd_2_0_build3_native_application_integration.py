from pathlib import Path
import importlib.util, sys
from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import person_page, render_get

MODULE=Path(__file__).parents[1]/"macos_app"/"build_app.py"
spec=importlib.util.spec_from_file_location("rc_b3",MODULE)
m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)

def test_build3_identity_preserves_engine():
    assert int(m.APP_BUILD)>=3
    assert m.APP_RELEASE.startswith("FFD 2.0 Build ")
    assert m.ENGINE_BASELINE=="FFD 1.9 RC1"

def test_native_edit_and_reload_menus():
    s=m.swift_source(Path("/tmp/Reunion Companion"))
    for x in ['NSMenu(title:"Edit")','"Cut"','"Copy"','"Paste"','"Select All"','NSMenu(title:"View")','"Reload"']:
        assert x in s
    assert "webView?.reload()" in s

def test_native_diagnostics_contract():
    s=m.swift_source(Path("/tmp/Reunion Companion"))
    assert '"Diagnostics…"' in s
    assert "isCompanionReady()" in s
    assert "isOllamaReady()" in s
    assert ".reunion-companion/companion.sqlite3" in s
    assert "backend.log" in s
    assert "REUNION_LLM_MODEL" in s
    assert "FFD 1.9 RC1" in s

def seed(db):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(1,'@I1@',1,'Test','Person','Test Person','M','Test /Person/')")
    db.execute("INSERT INTO notes(id,person_id,note_type,gedcom_tag,text) VALUES(1,1,'Misc','NOTE','A recorded life note.')")
    db.commit()

def test_presentation_biography_exposes_explicit_regenerate_control(tmp_path):
    db=connect(tmp_path/"x.sqlite3"); seed(db)
    html=person_page(db,1,"biography",presentation_override=True)
    assert "Regenerate Biography" in html
    assert "?force=1" in html
    assert "loadBiography(false)" in html

def test_narrative_endpoint_accepts_force_without_changing_default_contract(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.sqlite3"); seed(db)
    calls=[]
    def fake(db,pid,client=None,force=False):
        calls.append(force); return {"narrative":"Biography text"}
    import reunion_companion.companion.person_narrative as pn
    monkeypatch.setattr(pn,"person_narrative",fake)
    assert "Biography text" in render_get(db,"/person-narrative/1",{})
    assert calls[-1] is False
    assert "Biography text" in render_get(db,"/person-narrative/1",{"force":"1"})
    assert calls[-1] is True

def test_shell_identity_matches_build3():
    from reunion_companion import app_identity
    assert app_identity.APP_SERIES=="2.0"
    assert int(app_identity.APP_BUILD)>=3
    assert app_identity.ENGINE_BASELINE=="FFD 1.9 RC1"
