from pathlib import Path

from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import person_page, descendant_report_page, family_page
from reunion_companion.companion.beta3_publishing import standalone_descendant_report_output
from test_ffd_2_0_rc1_0_11_2_unified_family_charts_html_book_qa_pass_2 import _seed


def test_release_identity_is_rc1_0_12_2():
    s=Path("macos_app/build_app.py").read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.12.2 — Descendant Report Controls & Presentation QA"' in s


def test_person_publish_replaces_old_family_report_with_descendant_report(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=person_page(db,3,"publish")
    assert "Descendant Report…" in html
    assert "/descendant-report/3" in html
    assert "Family Report (HTML)" not in html
    db.close()


def test_person_family_list_preselects_descendant_report_family(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=person_page(db,3,"publish")
    assert "/descendant-report/3" in html
    assert "Descendant Report…" in html
    db.close()


def test_descendant_report_configuration_has_family_generation_and_output_controls(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=descendant_report_page(db,3,{"family":"101","generations":"5"})
    assert "<h1>Descendant Report</h1>" in html
    assert "type='hidden' name='family_id' value='101'" in html
    assert "Starting family" in html
    assert "Line Son and Line Wife" in html
    assert "name='generations'" in html
    assert "value='5' selected" in html
    for n in range(1,7):
        assert f"value='{n}'" in html
    assert "Create Print-ready PDF" in html
    assert "Create HTML" in html
    assert "/publish/person/3/descendant-report" in html
    db.close()


def test_descendant_report_configuration_clamps_generation_query_to_supported_range(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=descendant_report_page(db,3,{"family":"101","generations":"99"})
    assert "value='6' selected" in html
    db.close()


def test_family_workspace_links_to_same_descendant_configuration(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=family_page(db,101)
    assert "Configure Descendant Report…" in html
    assert "/descendant-report/3?family=101" in html
    db.close()


def test_standalone_service_supports_pdf_output(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    import reunion_companion.companion.beta3_publishing as pub
    target=tmp_path/"descendants.pdf";target.write_bytes(b"%PDF")
    called={}
    def fake_pdf(db_arg,start_pid,path,generations,family_id,theme):
        called.update(start_pid=start_pid,generations=generations,family_id=family_id)
        return target
    monkeypatch.setattr(pub,"write_descendant_report_pdf",fake_pdf)
    out=standalone_descendant_report_output(db,3,"Line Son",5,101,"PDF")
    assert out.endswith("descendants.pdf")
    assert called == {"start_pid":3,"generations":5,"family_id":101}
    row=db.execute("SELECT kind,output_format FROM companion_publication_history ORDER BY id DESC LIMIT 1").fetchone()
    assert row["kind"]=="Descendant Report"
    assert row["output_format"]=="PDF"
    db.close()


def test_descendant_report_logo_has_explicit_print_safe_size():
    s=Path("src/reunion_companion/companion/descendant_report.py").read_text()
    assert ".descendant-report-title .publishing-mark { width:28mm; height:28mm;" in s


def test_report_body_structure_is_not_replaced_by_controls_pass():
    s=Path("src/reunion_companion/companion/descendant_report.py").read_text()
    assert "desc-family generation-" in s
    assert "desc-children" in s
    assert "desc-subfamilies" in s
    assert "Generation 1 is the selected starting couple" in s
