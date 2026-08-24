from pathlib import Path
from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import render_get
from reunion_companion.companion.beta3_data_manager import ensure_companion_tables
from reunion_companion.companion.beta3_publishing import delete_publication


def test_global_nav_is_companion_sidebar_before_person_selection(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    html=render_get(db,'/reports',{})
    sidebar=html.split("<aside class='rc-sidebar'>",1)[1].split('</aside>',1)[0]
    assert "href='/'>Home</a>" in sidebar
    assert "href='/search'>Search</a>" in sidebar
    assert "href='/questions'>Ask</a>" not in sidebar
    assert "href='/search'>People</a>" not in sidebar
    assert "href='/research'>Research</a>" not in sidebar
    assert "href='/publishing'>Publishing</a>" not in sidebar
    db.close()


def test_research_home_uses_persistent_sidebar_instead_of_duplicate_explore_boxes(tmp_path):
    from reunion_companion.companion.ffd_presentation import (
        presentation_mode_enabled,
        set_presentation_mode,
    )

    db=connect(tmp_path/'x.sqlite3')
    previous=presentation_mode_enabled()
    try:
        set_presentation_mode(False)
        html=render_get(db,'/',{})
        sidebar=html.split("<aside class='rc-sidebar'>",1)[1].split('</aside>',1)[0]
        for label in ('Research','Priorities','Improve','Manage','Reports'):
            assert label in sidebar
        assert 'Research Priorities' not in html
        assert 'Improve the Data' not in html
        assert 'Data Manager' not in html
    finally:
        set_presentation_mode(previous)
        db.close()


def test_delete_report_removes_dedicated_assets(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); ensure_companion_tables(db)
    report=tmp_path/'Charles-book.html'; report.write_text('report')
    assets=tmp_path/'Charles-book_assets'; assets.mkdir(); (assets/'photo.jpg').write_bytes(b'x')
    db.execute("INSERT INTO companion_publication_history(created_at,kind,subject,output_path,output_format) VALUES('now','Book','Charles',?,'HTML')",(str(report),)); db.commit()
    hid=db.execute('SELECT max(id) FROM companion_publication_history').fetchone()[0]
    assert delete_publication(db,hid)
    assert not report.exists(); assert not assets.exists()
    db.close()


def test_legacy_publishing_route_is_reports(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    assert '<h1>Reports</h1>' in render_get(db,'/publishing',{})
    assert '<h1>Reports</h1>' in render_get(db,'/reports',{})
    db.close()
