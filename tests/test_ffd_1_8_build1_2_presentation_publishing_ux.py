from pathlib import Path
from reunion_companion.companion.person_navigation import PRESENTATION_ITEMS,RESEARCH_ITEMS,nav_html
from reunion_companion.companion.database import connect
from reunion_companion.companion.beta3_publishing import publication_history
from reunion_companion.companion.ffd_person_story import _events

def test_presentation_navigation_order_and_publish_last():
    assert [x[1] for x in PRESENTATION_ITEMS] == ["Overview","Interactive Family Chart","Timeline","Biography","Family","Media","Sources","Ask about the Family","Publish"]

def test_research_navigation_order_and_publish_last():
    labels=[x[1] for x in RESEARCH_ITEMS]
    assert labels[-5:]==["Confidence","Research","Data Quality","Ask about the Family","Publish"]

def test_navigation_uses_questions_route():
    h=nav_html(7,True,"ask");assert "/questions?person=7" in h and "class='active'" in h

def test_publication_history_defaults_to_ten(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    from reunion_companion.companion.beta3_data_manager import ensure_companion_tables
    ensure_companion_tables(db)
    for i in range(15): db.execute("INSERT INTO companion_publication_history(created_at,kind,subject,output_path,output_format) VALUES(?,?,?,?,?)",(str(i),'Report','P',f'/tmp/{i}.html','HTML'))
    db.commit();assert len(publication_history(db))==10

def test_changed_metadata_filter_contract():
    from reunion_companion.companion.beta_ui import _displayable_events
    rows=[{'event_type':'Changed','gedcom_tag':'CHAN'},{'event_type':'Birth','gedcom_tag':'BIRT'}]
    assert [x['event_type'] for x in _displayable_events(rows)]==['Birth']

def test_publish_is_last_in_both_modes():
    assert PRESENTATION_ITEMS[-1][0]=='publish' and RESEARCH_ITEMS[-1][0]=='publish'

def test_family_chart_is_shared_in_both_modes():
    assert PRESENTATION_ITEMS[1][0]=='family-chart' and RESEARCH_ITEMS[1][0]=='family-chart'
