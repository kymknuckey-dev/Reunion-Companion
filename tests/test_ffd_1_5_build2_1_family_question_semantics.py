from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question,interpret_question
def seed(db):
 ps=[(1,'@I1@',1,'Mervyn Neil','Knuckey','Mervyn Neil Knuckey','M','Mervyn Neil /Knuckey/'),(2,'@I2@',2,'Elaine Fay','Cox','Elaine Fay Cox','F','Elaine Fay /Cox/'),(3,'@I3@',3,'Victor Alexander','Knuckey','Victor Alexander Knuckey','M','Victor Alexander /Knuckey/'),(4,'@I4@',4,'Lois Aletha','Waight','Lois Aletha Waight','F','Lois Aletha /Waight/'),(5,'@I5@',5,'Kym Wayne','Knuckey','Kym Wayne Knuckey','M','Kym Wayne /Knuckey/'),(6,'@I6@',6,'Jodie Karen','Knuckey','Jodie Karen Knuckey','F','Jodie Karen /Knuckey/'),(7,'@I7@',7,'Jamie Lee','Knuckey','Jamie Lee Knuckey','M','Jamie Lee /Knuckey/'),(8,'@I8@',8,'Brian Victor','Knuckey','Brian Victor Knuckey','M','Brian Victor /Knuckey/'),(9,'@I9@',9,'Susan Lee','Jones','Susan Lee Jones','F','Susan Lee /Jones/')]
 db.executemany("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",ps)
 for f in (1,2,3):db.execute("INSERT INTO families(id,gedcom_xref) VALUES(?,?)",(f,f'@F{f}@'))
 for r in [(1,1,'Husband'),(1,2,'Wife'),(1,5,'Child'),(1,6,'Child'),(1,7,'Child'),(2,3,'Husband'),(2,4,'Wife'),(2,1,'Child'),(2,8,'Child'),(3,5,'Husband'),(3,9,'Wife')]:db.execute("INSERT INTO family_members VALUES(?,?,?)",r)
 db.commit()
def test_intents():
 assert interpret_question("Does Mervyn have a brother?")=="siblings"
 assert interpret_question("Who is Mervyn's father?")=="father"
 assert interpret_question("Who is Mervyn's mother?")=="mother"
def test_third_child(tmp_path):
 db=connect(tmp_path/"x");seed(db);r=answer_question(db,"Who is Mervyn's third child?",1)
 assert r["answer"]=="Mervyn Neil Knuckey’s 3rd child is Jamie Lee Knuckey."
def test_brother(tmp_path):
 db=connect(tmp_path/"x");seed(db);r=answer_question(db,"Does Mervyn Knuckey have a brother?",1)
 assert "Brian Victor Knuckey" in r["answer"] and "Jodie" not in r["answer"]
def test_sibling(tmp_path):
 db=connect(tmp_path/"x");seed(db);assert "Brian Victor Knuckey" in answer_question(db,"Who is Mervyn Knuckey sibling?",1)["answer"]
def test_father_only(tmp_path):
 db=connect(tmp_path/"x");seed(db);r=answer_question(db,"Who is Mervyn Knuckey's father?",1)
 assert r["answer"]=="Mervyn Neil Knuckey’s father: Victor Alexander Knuckey." and "Lois" not in r["answer"]
def test_mother_only(tmp_path):
 db=connect(tmp_path/"x");seed(db);assert answer_question(db,"Who is Mervyn's mother?",1)["answer"]=="Mervyn Neil Knuckey’s mother: Lois Aletha Waight."
def test_spouse_of_child_path_summary(tmp_path):
 db=connect(tmp_path/"x");seed(db);r=answer_question(db,"How is Mervyn Knuckey related to Susan Jones?",1)
 assert r["kind"]=="connection";assert r["answer"]=="Susan Lee Jones is the spouse of Mervyn Neil Knuckey’s child, Kym Wayne Knuckey.";assert r["path"]
