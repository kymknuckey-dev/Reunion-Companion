from reunion_companion.companion.database import connect
from reunion_companion.companion.external_research_runner import recover_transport_failures

def test_recover_known_obsolete_form_failure(tmp_path):
    db=connect(tmp_path/"x.db")
    db.execute("INSERT INTO companion_external_scan_queue(source_name,person_gedcom_xref,person_name_snapshot,status,attempts,last_error) VALUES('Ryerson','@I1@','Charles','failed',1,'surname field not found')")
    db.commit()
    assert recover_transport_failures(db)==1
    r=db.execute("SELECT status,attempts,last_error FROM companion_external_scan_queue").fetchone()
    assert r["status"]=="queued"
    assert r["attempts"]==0
    assert r["last_error"] is None

def test_does_not_recover_unrelated_failure(tmp_path):
    db=connect(tmp_path/"x.db")
    db.execute("INSERT INTO companion_external_scan_queue(source_name,person_gedcom_xref,person_name_snapshot,status,attempts,last_error) VALUES('Ryerson','@I1@','Charles','failed',1,'unexpected parser failure')")
    db.commit()
    assert recover_transport_failures(db)==0
    r=db.execute("SELECT status,last_error FROM companion_external_scan_queue").fetchone()
    assert r["status"]=="failed"
    assert r["last_error"]=="unexpected parser failure"
