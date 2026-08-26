from reunion_companion.companion.database import connect
from reunion_companion.companion import research_priority


def _person(db,pid,name):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,f"@I{pid}@",pid,name,"Test",f"{name} Test","U",f"{name} /Test/"),
    )


def _family(db,fid,parent,child):
    db.execute("INSERT INTO families(id,gedcom_xref) VALUES(?,?)",(fid,f"@F{fid}@"))
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'HUSB')",(fid,parent))
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'CHIL')",(fid,child))


def test_priority_map_builds_adjacency_once(monkeypatch,tmp_path):
    db=connect(tmp_path/"x.db")
    for pid,name in ((1,"Focus"),(2,"Child"),(3,"Grandchild"),(4,"Other")):
        _person(db,pid,name)
    _family(db,1,1,2); _family(db,2,2,3); db.commit()

    import reunion_companion.companion.knowledge_graph as kg
    real=kg.adjacency
    calls={"n":0}
    def counted(db):
        calls["n"]+=1
        return real(db)
    monkeypatch.setattr(kg,"adjacency",counted)

    rels=research_priority.priority_map(db,1,[1,2,3,4])
    assert calls["n"]==1
    assert rels[1]["distance"]==0
    assert rels[2]["distance"]==1
    assert rels[3]["distance"]==2
    assert rels[4]["distance"] is None


def test_bulk_sort_preserves_nearest_first(tmp_path):
    db=connect(tmp_path/"x.db")
    for pid,name in ((1,"Focus"),(2,"Child"),(3,"Grandchild"),(4,"Other")):
        _person(db,pid,name)
    _family(db,1,1,2); _family(db,2,2,3); db.commit()
    rows=[
        {"id":4,"display_name":"Other Test"},
        {"id":3,"display_name":"Grandchild Test"},
        {"id":2,"display_name":"Child Test"},
    ]
    ordered,rels=research_priority.sort_rows_by_focus(db,1,rows,"id")
    assert [r["id"] for r in ordered]==[2,3,4]
    assert rels[2]["distance"]==1
    assert rels[3]["distance"]==2
    assert rels[4]["distance"] is None
