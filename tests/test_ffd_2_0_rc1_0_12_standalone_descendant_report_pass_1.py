from pathlib import Path

import pytest

from reunion_companion.companion.database import connect
from reunion_companion.companion.descendant_report import (
    descendant_report_model,
    descendant_report_html,
    write_descendant_report,
)
from reunion_companion.companion.beta3_publishing import standalone_descendant_report_output
from test_ffd_2_0_rc1_0_11_2_unified_family_charts_html_book_qa_pass_2 import _person, _family


def _seed(db):
    names={
        1:("Start Husband","M"),2:("Start Wife","F"),
        3:("Child One","M"),4:("Child Two","F"),
        5:("Child One Spouse","F"),6:("Grandchild One","F"),7:("Grandchild Two","M"),
        8:("Grandchild Spouse","F"),9:("Great Grandchild","F"),
        10:("Child Two Spouse","M"),11:("Other Grandchild","M"),
    }
    for pid,(name,sex) in names.items(): _person(db,pid,name,sex)
    _family(db,100,1,2,(3,4),"1950","Adelaide")
    _family(db,101,3,5,(6,7),"1975","Brighton")
    _family(db,102,7,8,(9,),"2000","Glenelg")
    _family(db,103,10,4,(11,),"1978","Marion")
    db.commit()


def test_release_identity_is_rc1_0_12():
    s=Path("macos_app/build_app.py").read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.12 — Standalone Descendant Report Pass 1"' in s


def test_generation_one_is_starting_couple_only(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    model=descendant_report_model(db,1,1)
    assert model["tree"]["generation"] == 1
    assert model["tree"]["husband"]["display_name"] == "Start Husband"
    assert model["tree"]["wife"]["display_name"] == "Start Wife"
    assert model["tree"]["children"] == []
    db.close()


def test_generation_two_adds_children_and_spouse_families(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    model=descendant_report_model(db,1,2)
    children=model["tree"]["children"]
    assert [x["person"]["display_name"] for x in children] == ["Child One","Child Two"]
    assert children[0]["families"][0]["generation"] == 2
    assert children[0]["families"][0]["wife"]["display_name"] == "Child One Spouse"
    assert children[0]["families"][0]["children"] == []
    db.close()


def test_generation_three_reaches_grandchildren_but_not_great_grandchildren(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=descendant_report_html(db,1,3)
    assert "Grandchild One" in html
    assert "Grandchild Two" in html
    assert "Other Grandchild" in html
    assert "Great Grandchild" not in html
    assert "Generation 3" in html
    db.close()


def test_generation_four_reaches_great_grandchildren(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=descendant_report_html(db,1,4)
    assert "Great Grandchild" in html
    # An unmarried terminal descendant is shown at the requested depth without
    # inventing a spouse-family header solely to display "Generation 4".
    assert "Grandchild Two" in html
    db.close()


@pytest.mark.parametrize("depth",[0,7,"bad"])
def test_generation_depth_is_bounded(depth,tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    with pytest.raises(ValueError):
        descendant_report_model(db,1,depth)
    db.close()


def test_multiple_starting_families_require_explicit_family_choice(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    _person(db,12,"Second Wife","F")
    _family(db,104,1,12,(),"1960","Adelaide")
    db.commit()
    with pytest.raises(ValueError,match="more than one family"):
        descendant_report_model(db,1,3)
    model=descendant_report_model(db,1,3,family_id=100)
    assert model["start_family"]["id"] == 100
    db.close()


def test_html_uses_indented_family_report_presentation(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=descendant_report_html(db,1,4)
    assert "<h1>Descendant Report</h1>" in html
    assert "Start Husband &amp; Start Wife" in html
    assert "desc-family generation-1" in html
    assert "desc-children" in html
    assert "desc-subfamilies" in html
    assert "border-left:1px solid #aaa" in html
    assert "background:" not in html.split("REPORT_CSS",1)[0]  # no colour-box design dependency
    db.close()


def test_report_writes_html_file(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    p=write_descendant_report(db,1,tmp_path/"descendants.html",3)
    assert p.exists()
    text=p.read_text()
    assert "Descendant Report" in text
    assert "Grandchild One" in text
    db.close()


def test_service_records_standalone_descendant_report_without_publish_ui_change(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    import reunion_companion.companion.beta3_publishing as pub
    monkeypatch.setattr(pub,"write_descendant_report",lambda *a,**k: tmp_path/"standalone.html")
    (tmp_path/"standalone.html").write_text("ok")
    path=standalone_descendant_report_output(db,1,"Start Husband",3,100,"HTML")
    assert path.endswith("standalone.html")
    row=db.execute("SELECT kind,output_format FROM companion_publication_history ORDER BY id DESC LIMIT 1").fetchone()
    assert row["kind"] == "Descendant Report"
    assert row["output_format"] == "HTML"
    ui=Path("src/reunion_companion/companion/beta_ui.py").read_text()
    assert "Standalone Descendant Report" not in ui
    db.close()


def test_history_book_scope_and_spouse_chart_modules_remain_separate():
    report=Path("src/reunion_companion/companion/descendant_report.py").read_text()
    assert "family_book_scope" not in report
    assert "spouse_context_chart" not in report


def test_existing_family_descendant_chart_action_uses_new_standalone_renderer(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    import reunion_companion.companion.beta3_publishing as pub
    target=tmp_path/"family_descendants.html"
    target.write_text("descendant report")
    called={}
    def fake_write(db_arg,start_pid,path,generations,family_id,theme):
        called.update(start_pid=start_pid,generations=generations,family_id=family_id)
        return target
    monkeypatch.setattr(pub,"write_descendant_report",fake_write)
    out=pub.descendant_chart(db,100,"Start Family",4)
    assert out.endswith("family_descendants.html")
    assert called == {"start_pid":1,"generations":4,"family_id":100}
    row=db.execute("SELECT kind,output_format FROM companion_publication_history ORDER BY id DESC LIMIT 1").fetchone()
    assert row["kind"] == "Descendant Report"
    assert row["output_format"] == "HTML"
    db.close()
