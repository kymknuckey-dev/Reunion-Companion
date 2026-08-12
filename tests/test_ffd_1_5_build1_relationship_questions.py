from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question,blood_relationship
from reunion_companion.companion.beta_ui import render_get
from reunion_companion.companion.ffd_presentation import set_presentation_mode
def seed(db):
 people=[(1,'@I1@',1,'Mervyn','Knuckey','Mervyn Knuckey','M','Mervyn /Knuckey/'),(2,'@I2@',2,'Elaine','Cox','Elaine Cox','F','Elaine /Cox/'),(3,'@I3@',3,'Victor','Knuckey','Victor Knuckey','M','Victor /Knuckey/'),(4,'@I4@',4,'Lois','Waight','Lois Waight','F','Lois /Waight/'),(5,'@I5@',5,'James','Knuckey','James Knuckey','M','James /Knuckey/'),(6,'@I6@',6,'Elizabeth','Hunter','Elizabeth Hunter','F','Elizabeth /Hunter/'),(7,'@I7@',7,'Kym','Knuckey','Kym Knuckey','M','Kym /Knuckey/'),(8,'@I8@',8,'Brian','Knuckey','Brian Knuckey','M','Brian /Knuckey/')]
 db.executemany("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",people)
 for fid in (1,2,3):db.execute("INSERT INTO families(id,gedcom_xref) VALUES(?,?)",(fid,f'@F{fid}@'))
 for r in [(1,1,'Husband'),(1,2,'Wife'),(1,7,'Child'),(1,8,'Child'),(2,3,'Husband'),(2,4,'Wife'),(2,1,'Child'),(3,5,'Husband'),(3,6,'Wife'),(3,3,'Child')]:db.execute("INSERT INTO family_members VALUES(?,?,?)",r)
 db.commit()
def test_ancestor(tmp_path):
 db=connect(tmp_path/"x.sqlite3");seed(db);r=blood_relationship(db,1,5);assert r["label"]=="grandfather";assert len(r["path"])==3
def test_descendant(tmp_path):
 db=connect(tmp_path/"x.sqlite3");seed(db);assert blood_relationship(db,3,7)["label"]=="grandson"
def test_sibling(tmp_path):
 db=connect(tmp_path/"x.sqlite3");seed(db);assert blood_relationship(db,7,8)["label"]=="brother"
def test_parents(tmp_path):
 db=connect(tmp_path/"x.sqlite3");seed(db);r=answer_question(db,"Who were Mervyn Knuckey's parents?");assert {p["display_name"] for p in r["people"]}=={"Victor Knuckey","Lois Waight"}
def test_spouse(tmp_path):
 db=connect(tmp_path/"x.sqlite3");seed(db);assert answer_question(db,"Who did Victor Knuckey marry?")["people"][0]["display_name"]=="Lois Waight"
def test_relationship_question(tmp_path):
 db=connect(tmp_path/"x.sqlite3");seed(db);r=answer_question(db,"How is Mervyn Knuckey related to James Knuckey?");assert r["label"]=="grandfather"
def test_page(tmp_path,monkeypatch):
 monkeypatch.setenv("HOME",str(tmp_path));db=connect(tmp_path/"x.sqlite3");seed(db);set_presentation_mode(True);p=render_get(db,"/questions",{"person":"1","q":"Who were Mervyn Knuckey's parents?"});assert "Relationship questions" in p and "Victor Knuckey" in p
def test_presentation_only(tmp_path,monkeypatch):
 monkeypatch.setenv("HOME",str(tmp_path));db=connect(tmp_path/"x.sqlite3");seed(db);set_presentation_mode(False);assert "Ask about the family" in render_get(db,"/questions",{})
