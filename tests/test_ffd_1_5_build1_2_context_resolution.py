from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question
def seed(db):
 ps=[(1,'@I1@',1,'Mervyn Neil','Knuckey','Mervyn Neil Knuckey','M','Mervyn Neil /Knuckey/'),(2,'@I2@',2,'Elaine Fay','Cox','Elaine Fay Cox','F','Elaine Fay /Cox/'),(3,'@I3@',3,'Victor Alexander','Knuckey','Victor Alexander Knuckey','M','Victor Alexander /Knuckey/'),(4,'@I4@',4,'Lois Aletha','Waight','Lois Aletha Waight','F','Lois Aletha /Waight/'),(5,'@I5@',5,'Mervyn','Knuckey','Mervyn Knuckey','M','Mervyn /Knuckey/'),(6,'@I6@',6,'Victor','Knuckey','Victor Knuckey','M','Victor /Knuckey/'),(7,'@I7@',7,'Verna Gladders','Knuckey','Verna Gladders Knuckey','M','Verna Gladders /Knuckey/'),(8,'@I8@',8,'Catherine','Biggar','Catherine Biggar','F','Catherine /Biggar/'),(9,'@I9@',9,'Florence Maud','Drayton','Florence Maud Drayton','F','Florence Maud /Drayton/'),(10,'@I10@',10,'Kym Wayne','Knuckey','Kym Wayne Knuckey','M','Kym Wayne /Knuckey/')]
 db.executemany("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",ps)
 for f in range(1,6):db.execute("INSERT INTO families(id,gedcom_xref) VALUES(?,?)",(f,f'@F{f}@'))
 for r in [(1,1,'Husband'),(1,2,'Wife'),(1,10,'Child'),(2,3,'Husband'),(2,4,'Wife'),(2,1,'Child'),(3,7,'Husband'),(3,8,'Wife'),(3,5,'Child'),(4,6,'Husband'),(4,9,'Wife'),(5,7,'Husband'),(5,6,'Child')]:db.execute("INSERT INTO family_members VALUES(?,?,?)",r)
 db.commit()
def test_current_person_wins(tmp_path):
 db=connect(tmp_path/"x");seed(db);assert answer_question(db,"Who were Mervyn Knuckey's parents?",1)["answer"]=="Mervyn Neil Knuckey’s parents: Victor Alexander Knuckey, Lois Aletha Waight."
def test_current_children(tmp_path):
 db=connect(tmp_path/"x");seed(db);assert answer_question(db,"Who are Mervyn Knuckey's children?",1)["answer"]=="Mervyn Neil Knuckey’s children: Kym Wayne Knuckey."
def test_second_name_uses_proximity(tmp_path):
 db=connect(tmp_path/"x");seed(db);assert answer_question(db,"How is Mervyn Knuckey related to Victor Knuckey?",1)["answer"]=="Victor Alexander Knuckey is Mervyn Neil Knuckey’s father."
def test_other_name_uses_proximity(tmp_path):
 db=connect(tmp_path/"x");seed(db);assert answer_question(db,"Who did Victor Knuckey marry?",1)["answer"]=="Victor Alexander Knuckey’s recorded spouse: Lois Aletha Waight."
def test_without_context_literal_name_wins(tmp_path):
 db=connect(tmp_path/"x");seed(db);assert answer_question(db,"Who did Victor Knuckey marry?")["answer"]=="Victor Knuckey’s recorded spouse: Florence Maud Drayton."
def test_equal_distance_remains_ambiguous(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 for pid,g in [(20,'Alex One'),(21,'Alex Two')]:
  db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",(pid,f'@I{pid}@',pid,g,'Knuckey',g+' Knuckey','M',g+' /Knuckey/'))
  db.execute("INSERT INTO families(id,gedcom_xref) VALUES(?,?)",(pid,f'@F{pid}@'));db.execute("INSERT INTO family_members VALUES(?,?,?)",(pid,1,'Husband'));db.execute("INSERT INTO family_members VALUES(?,?,?)",(pid,pid,'Child'))
 db.commit();assert answer_question(db,"Who are Alex Knuckey's parents?",1)["status"]=="ambiguous"
