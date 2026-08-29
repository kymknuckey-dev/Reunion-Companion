import json

from reunion_companion.companion import beta_ui
from reunion_companion.companion.database import connect
from reunion_companion.companion.beta3_data_manager import ensure_companion_tables, import_history, import_history_count
from reunion_companion.companion.ryerson_targeted_bootstrap import ensure_targeted_schema


def _stub_crawler_status(monkeypatch):
    import reunion_companion.companion.external_research_runner as runner
    import reunion_companion.companion.ryerson_targeted_bootstrap as targeted
    monkeypatch.setattr(runner,'runner_status',lambda db:{
        'enabled':False,'source_waiting':False,'total':0,'queued':0,'searching':0,
        'retry_wait':0,'findings':0,'no_match':0,'failed':0,
    })
    monkeypatch.setattr(targeted,'targeted_status',lambda db:{
        'enabled':False,'completed':0,'queued':0,'retry_wait':0,
        'searching':0,'failed':0,'total':0,'core_surnames':['Knuckey'],
    })


def test_import_history_supports_limit_offset_and_count(tmp_path):
    db=connect(tmp_path/'x.db')
    ensure_companion_tables(db)
    for i in range(23):
        db.execute(
            "INSERT INTO companion_import_history(source_path,imported_at,counts_json,diff_json,status) VALUES(?,?,?,?,?)",
            (f'/tmp/import-{i:02}.ged',f'2026-08-29T{i%24:02}:00:00+09:30',json.dumps({}),json.dumps({}),'success'),
        )
    db.commit()
    assert import_history_count(db)==23
    page2=import_history(db,limit=10,offset=10)
    assert len(page2)==10
    assert page2[0]['source_path'].endswith('import-12.ged')
    assert page2[-1]['source_path'].endswith('import-03.ged')


def test_manage_import_history_is_ten_rows_per_page(monkeypatch,tmp_path):
    db=connect(tmp_path/'x.db')
    ensure_companion_tables(db)
    for i in range(23):
        db.execute(
            "INSERT INTO companion_import_history(source_path,imported_at,counts_json,diff_json,status) VALUES(?,?,?,?,?)",
            (f'/tmp/import-{i:02}.ged',f'2026-08-29T{i%24:02}:00:00+09:30',json.dumps({}),json.dumps({}),'success'),
        )
    db.commit()
    _stub_crawler_status(monkeypatch)
    monkeypatch.setattr(beta_ui,'_ryerson_recent_activity',lambda db,limit=3:[])

    first=beta_ui.data_page(db,import_page=1)
    assert 'Page 1 of 3' in first
    assert "href='/data?import_page=2'>Next</a>" in first
    assert "import-22.ged" in first and "import-13.ged" in first
    assert "import-12.ged" not in first

    second=beta_ui.data_page(db,import_page=2)
    assert 'Page 2 of 3' in second
    assert "href='/data?import_page=1'>Previous</a>" in second
    assert "href='/data?import_page=3'>Next</a>" in second
    history_section=second.split("<div class='card'><h2>Import History</h2>",1)[1]
    assert "import-12.ged" in history_section and "import-03.ged" in history_section
    assert "import-22.ged" not in history_section


def test_render_get_accepts_import_history_page_query(monkeypatch,tmp_path):
    db=connect(tmp_path/'x.db')
    seen={}
    monkeypatch.setattr(beta_ui,'data_page',lambda db,**kwargs: seen.update(kwargs) or 'ok')
    assert beta_ui.render_get(db,'/data',{'import_page':'4'})=='ok'
    assert seen['import_page']==4


def test_recent_crawler_activity_returns_three_newest_persisted_attempts(monkeypatch,tmp_path):
    db=connect(tmp_path/'x.db')
    ensure_targeted_schema(db)
    rows=[
        ('name','Gill','Mary','name:gill|mary','completed','2026-08-29T04:28:00+00:00','',31,4),
        ('name','Gilbert','Alice','name:gilbert|alice','completed','2026-08-29T04:26:00+00:00','',8,0),
        ('name','Gillingwater','William','name:gillingwater|william','retry_wait','2026-08-29T04:30:00+00:00','Ryerson server overloaded',0,0),
        ('name','Giles','Charles','name:giles|charles','completed','2026-08-29T04:24:00+00:00','',22,2),
    ]
    for kind,surname,given,key,status,at,error,results,matches in rows:
        db.execute(
            "INSERT INTO companion_ryerson_targeted_queue(search_kind,surname,given_name,search_key,status,last_attempt_at,last_error,result_count,match_count) VALUES(?,?,?,?,?,?,?,?,?)",
            (kind,surname,given,key,status,at,error,results,matches),
        )
    db.commit()
    monkeypatch.setattr(beta_ui,'_local_activity_time',lambda value:value[11:16])
    recent=beta_ui._ryerson_recent_activity(db,3)
    assert [x['name'] for x in recent]==['William Gillingwater','Mary Gill','Alice Gilbert']
    assert recent[0]['time']=='04:30'
    assert recent[0]['status']=='Waiting'
    assert recent[0]['outcome']=='Ryerson server overloaded'
    assert recent[1]['outcome']=='4 matches from 31 results'
    assert recent[2]['outcome']=='No matches'


def test_manage_renders_timestamped_recent_activity(monkeypatch,tmp_path):
    db=connect(tmp_path/'x.db')
    _stub_crawler_status(monkeypatch)
    monkeypatch.setattr(beta_ui,'_ryerson_recent_activity',lambda db,limit=3:[
        {'time':'14:00','name':'William Gillingwater','status':'Waiting','outcome':'Ryerson server overloaded'},
        {'time':'13:58','name':'Mary Gill','status':'Completed','outcome':'4 matches from 31 results'},
        {'time':'13:56','name':'Alice Gilbert','status':'Completed','outcome':'No matches'},
    ])
    html=beta_ui.data_page(db)
    assert 'Recent crawler activity' in html
    assert '14:00' in html and 'William Gillingwater' in html
    assert 'Waiting · Ryerson server overloaded' in html
    assert '13:58' in html and '4 matches from 31 results' in html
    assert '13:56' in html and 'No matches' in html
