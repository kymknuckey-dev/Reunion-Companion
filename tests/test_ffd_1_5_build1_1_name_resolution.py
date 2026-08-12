from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question,resolve_name
def seed(db):
 people=[(1,'@I1@',1,'Mervyn Neil','Knuckey','Mervyn Neil Knuckey','M','Mervyn Neil /Knuckey/'),(2,'@I2@',2,'Elaine Fay','Cox','Elaine Fay Cox','F','Elaine Fay /Cox/'),(3,'@I3@',3,'Victor Alexander','Knuckey','Victor Alexander Knuckey','M','Victor Alexander /Knuckey/'),(4,'@I4@',4,'Lois Aletha','Waight','Lois Aletha Waight','F','Lois Aletha /Waight/'),(5,'@I5@',5,'James','Knuckey','James Knuckey','M','James /Knuckey/'),(7,'@I7@',7,'Kym Wayne','Knuckey','Kym Wayne Knuckey','M','Kym Wayne /Knuckey/'),(8,'@I8@',8,'Jodie Karen','Knuckey','Jodie Karen Knuckey','F','Jodie Karen /Knuckey/'),(9,'@I9@',9,'Jamie Lee','Knuckey','Jamie Lee Knuckey','M','Jamie Lee /Knuckey/')]
 db.executemany("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",people)
 for fid in (1,2,3):db.execute("INSERT INTO families(id,gedcom_xref) VALUES(?,?)",(fid,f'@F{fid}@'))
 for r in [(1,1,'Husband'),(1,2,'Wife'),(1,7,'Child'),(1,8,'Child'),(1,9,'Child'),(2,3,'Husband'),(2,4,'Wife'),(2,1,'Child'),(3,5,'Husband'),(3,3,'Child')]:db.execute("INSERT INTO family_members VALUES(?,?,?)",r)
 db.commit()
def test_short_names(tmp_path):
 db=connect(tmp_path/"x.sqlite3");seed(db)
 assert [p["display_name"] for p in resolve_name(db,"Mervyn Knuckey")]==["Mervyn Neil Knuckey"]
 assert [p["display_name"] for p in resolve_name(db,"Victor Knuckey")]==["Victor Alexander Knuckey"]
def test_relationship(tmp_path):
 db=connect(tmp_path/"x.sqlite3");seed(db);r=answer_question(db,"How is Mervyn Knuckey related to Victor Knuckey?")
 assert r["answer"]=="Victor Alexander Knuckey is Mervyn Neil Knuckey’s father."
def test_parent_possessive(tmp_path):
 db=connect(tmp_path/"x.sqlite3");seed(db);r=answer_question(db,"Who were Mervyn Knuckey's parents?")
 assert r["answer"]=="Mervyn Neil Knuckey’s parents: Victor Alexander Knuckey, Lois Aletha Waight."
def test_victor_overrides_context(tmp_path):
 db=connect(tmp_path/"x.sqlite3");seed(db);r=answer_question(db,"Who did Victor Knuckey marry?",subject_id=1)
 assert r["answer"]=="Victor Alexander Knuckey’s recorded spouse: Lois Aletha Waight."
def test_children(tmp_path):
 db=connect(tmp_path/"x.sqlite3");seed(db);r=answer_question(db,"Who are Mervyn Knuckey's children?",subject_id=1)
 assert r["answer"]=="Mervyn Neil Knuckey’s children: Kym Wayne Knuckey, Jodie Karen Knuckey, Jamie Lee Knuckey."
def test_ambiguity(tmp_path):
 db=connect(tmp_path/"x.sqlite3");seed(db);db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(20,'@I20@',20,'Victor Henry','Knuckey','Victor Henry Knuckey','M','Victor Henry /Knuckey/')");db.commit()
 r=answer_question(db,"Who did Victor Knuckey marry?",subject_id=1);assert r["status"]=="ok";assert r["answer"]=="Victor Alexander Knuckey’s recorded spouse: Lois Aletha Waight."
def test_context_fallback(tmp_path):
 db=connect(tmp_path/"x.sqlite3");seed(db);r=answer_question(db,"Who did he marry?",subject_id=1)
 assert r["answer"]=="Mervyn Neil Knuckey’s recorded spouse: Elaine Fay Cox."
