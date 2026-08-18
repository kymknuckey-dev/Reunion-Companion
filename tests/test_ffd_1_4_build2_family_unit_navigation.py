from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_family_chart import family_chart,_ancestor_relationship,_descendant_relationship
from reunion_companion.companion.beta_ui import render_get
from reunion_companion.companion.ffd_presentation import set_presentation_mode
def seed(db):
 people=[(1,'@I1@',1,'Mervyn','Knuckey','Mervyn Knuckey','M','Mervyn /Knuckey/'),(2,'@I2@',2,'Elaine','Cox','Elaine Cox','F','Elaine /Cox/'),(3,'@I3@',3,'Victor','Knuckey','Victor Knuckey','M','Victor /Knuckey/'),(4,'@I4@',4,'Lois','Waight','Lois Waight','F','Lois /Waight/'),(5,'@I5@',5,'James','Knuckey','James Knuckey','M','James /Knuckey/'),(6,'@I6@',6,'Elizabeth','Hunter','Elizabeth Hunter','F','Elizabeth /Hunter/'),(7,'@I7@',7,'Kym','Knuckey','Kym Knuckey','M','Kym /Knuckey/'),(8,'@I8@',8,'Jodie','Knuckey','Jodie Knuckey','F','Jodie /Knuckey/'),(9,'@I9@',9,'Anne','Smith','Anne Smith','F','Anne /Smith/'),(10,'@I10@',10,'Sophie','Knuckey','Sophie Knuckey','F','Sophie /Knuckey/')]
 db.executemany("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",people)
 for fid in range(1,5):db.execute("INSERT INTO families(id,gedcom_xref) VALUES(?,?)",(fid,f'@F{fid}@'))
 for r in [(1,1,'Husband'),(1,2,'Wife'),(1,7,'Child'),(1,8,'Child'),(2,3,'Husband'),(2,4,'Wife'),(2,1,'Child'),(3,5,'Husband'),(3,6,'Wife'),(3,3,'Child'),(4,7,'Husband'),(4,9,'Wife'),(4,10,'Child')]:db.execute("INSERT INTO family_members VALUES(?,?,?)",r)
 db.commit()
def test_selected_family(tmp_path):
 db=connect(tmp_path/"x.sqlite3");seed(db);u=family_chart(db,1)["selected_units"][0]
 assert {p["display_name"] for p in u["spouses"]}=={"Mervyn Knuckey","Elaine Cox"} and {p["display_name"] for p in u["children"]}=={"Kym Knuckey","Jodie Knuckey"}
def test_descendant_family(tmp_path):
 db=connect(tmp_path/"x.sqlite3");seed(db);units=family_chart(db,1)["descendant_units"];u=next(x for x in units if any(p["display_name"]=="Kym Knuckey" for p in x["spouses"]))
 assert {p["display_name"] for p in u["spouses"]}=={"Kym Knuckey","Anne Smith"} and {p["display_name"] for p in u["children"]}=={"Sophie Knuckey"}
def test_ancestor_family(tmp_path):
 db=connect(tmp_path/"x.sqlite3");seed(db);units=family_chart(db,1)["ancestor_units"];u=next(x for x in units if any(p["display_name"]=="Victor Knuckey" for p in x["spouses"]))
 assert {p["display_name"] for p in u["spouses"]}=={"Victor Knuckey","Lois Waight"} and "Mervyn Knuckey" in {p["display_name"] for p in u["children"]}
def test_compact_labels():
 assert _ancestor_relationship("M",3)=="Great-grandfather"
 assert _ancestor_relationship("M",15)=="13× Great-grandfather"
 assert _descendant_relationship("M",3)=="Great-grandson"
def test_navigation(tmp_path,monkeypatch):
 monkeypatch.setenv("HOME",str(tmp_path));db=connect(tmp_path/"x.sqlite3");seed(db);set_presentation_mode(True);p=render_get(db,"/person/1",{"tab":"family-chart","offset":"0"})
 assert "Previous Generations" in p and "Later Generations" in p and "Selected family" in p
def test_research_unchanged(tmp_path,monkeypatch):
 monkeypatch.setenv("HOME",str(tmp_path));db=connect(tmp_path/"x.sqlite3");seed(db);set_presentation_mode(False);p=render_get(db,"/person/1",{});main=p.split("<main>",1)[1].split("</main>",1)[0];assert "Person Overview" in main;assert "Interactive Family Chart" not in main
