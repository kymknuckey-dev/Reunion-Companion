import sqlite3
from reunion_companion.companion.external_evidence import ensure_external_evidence, add_external_evidence, consolidate_external_evidence_duplicates
from reunion_companion.companion.ryerson_discovery_review import ensure_discovery_review_schema, remember_discovery, set_discovery_state


def db():
    d=sqlite3.connect(':memory:'); d.row_factory=sqlite3.Row
    ensure_external_evidence(d); ensure_discovery_review_schema(d); return d


def test_reinterpretation_does_not_resurrect_reviewed_record():
    d=db()
    row=remember_discovery(d,person_id=7,source_name='Ryerson',external_record_key='ryerson:14',proposed_fact_key='death:26JUL2012',match_confidence=75,now='2026-01-01')
    set_discovery_state(d,row['id'],'confirmed_complete',now='2026-01-02')
    again=remember_discovery(d,person_id=7,source_name='Ryerson',external_record_key='ryerson:14',proposed_fact_key='',match_confidence=75,now='2026-01-03')
    rows=d.execute("select * from companion_external_discovery_review").fetchall()
    assert len(rows)==1
    assert again['state']=='confirmed_complete'
    assert again['proposed_fact_key']=='death:26JUL2012'


def test_historical_review_duplicates_collapse_to_reviewed_state():
    d=db()
    d.execute("INSERT INTO companion_external_discovery_review(person_id,source_name,external_record_key,proposed_fact_key,match_confidence,state,decision_note,first_seen_at,updated_at) VALUES(1,'Ryerson','ryerson:14','death:26JUL2012',75,'confirmed_complete','done','a','b')")
    d.execute("INSERT INTO companion_external_discovery_review(person_id,source_name,external_record_key,proposed_fact_key,match_confidence,state,decision_note,first_seen_at,updated_at) VALUES(1,'Ryerson','ryerson:14','',75,'new','','c','d')")
    d.commit(); ensure_discovery_review_schema(d)
    rows=d.execute('select * from companion_external_discovery_review').fetchall()
    assert len(rows)==1 and rows[0]['state']=='confirmed_complete'


def test_historical_exact_evidence_duplicates_collapse_and_review_survives():
    d=db()
    # Deliberately bypass add_external_evidence to model a pre-dedupe database.
    vals=('I1','Brian Victor Knuckey','Ryerson','death_notice','Brian Victor KNUCKEY','Death','02JUN2018','Adelaide Advertiser','09JUN2018')
    for _ in range(4):
        d.execute("INSERT INTO companion_external_evidence(person_gedcom_xref,person_name_snapshot,source_name,evidence_type,source_record_name,event_type,event_date,publication,publication_date) VALUES(?,?,?,?,?,?,?,?,?)",vals)
    ids=[r['id'] for r in d.execute('select id from companion_external_evidence order by id')]
    for i,eid in enumerate(ids):
        r=remember_discovery(d,person_id=3,source_name='Ryerson',external_record_key=f'ryerson:{eid}',proposed_fact_key='death:02JUN2018',match_confidence=75)
        set_discovery_state(d,r['id'],'already_known')
    assert consolidate_external_evidence_duplicates(d)==3
    evidence=d.execute('select * from companion_external_evidence').fetchall()
    reviews=d.execute('select * from companion_external_discovery_review').fetchall()
    assert len(evidence)==1
    assert len(reviews)==1 and reviews[0]['state']=='already_known'
    assert reviews[0]['external_record_key']==f"ryerson:{evidence[0]['id']}"
