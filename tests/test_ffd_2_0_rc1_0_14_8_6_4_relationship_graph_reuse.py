from reunion_companion.companion.database import connect
from reunion_companion.companion.knowledge_graph import adjacency, relationship_path
from reunion_companion.companion.relationship_engine import interpret_relationship
from reunion_companion.companion import research_priority

def person(db,pid,name,sex="U"):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",(pid,f"@I{pid}@",pid,name,"Test",f"{name} Test",sex,f"{name} /Test/"))

def family(db,fid,parent,child):
    db.execute("INSERT INTO families(id,gedcom_xref) VALUES(?,?)",(fid,f"@F{fid}@"))
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'HUSB')",(fid,parent))
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'CHIL')",(fid,child))

def setup_family(db):
    person(db,1,"Focus","M"); person(db,2,"Child","M"); person(db,3,"Grandchild","F")
    family(db,1,1,2); family(db,2,2,3); db.commit()

def test_relationship_path_identical_with_prebuilt_adjacency(tmp_path):
    db=connect(tmp_path/"x.db"); setup_family(db)
    a=relationship_path(db,1,3); adj=adjacency(db); b=relationship_path(db,1,3,adj=adj)
    assert a==b

def test_interpret_relationship_identical_with_prebuilt_adjacency(tmp_path):
    db=connect(tmp_path/"x.db"); setup_family(db)
    a=interpret_relationship(db,1,3); adj=adjacency(db); b=interpret_relationship(db,1,3,adj=adj)
    assert a.label==b.label and a.reciprocal==b.reciprocal

def test_enrich_priority_labels_builds_adjacency_once(monkeypatch,tmp_path):
    db=connect(tmp_path/"x.db"); setup_family(db)
    rels=research_priority.priority_map(db,1,[2,3])
    import reunion_companion.companion.knowledge_graph as kg
    real=kg.adjacency; calls={"n":0}
    def counted(db):
        calls["n"]+=1
        return real(db)
    monkeypatch.setattr(kg,"adjacency",counted)
    research_priority.enrich_priority_labels(db,1,rels,[2,3])
    assert calls["n"]==1

def test_adjacency_uses_bulk_people_lookup_not_name_query_per_sort(tmp_path):
    db=connect(tmp_path/"x.db"); setup_family(db)
    seen=[]; db.set_trace_callback(seen.append); adjacency(db); db.set_trace_callback(None)
    people_selects=[q for q in seen if "SELECT" in q.upper() and "FROM PEOPLE" in q.upper()]
    assert len(people_selects)<=1
