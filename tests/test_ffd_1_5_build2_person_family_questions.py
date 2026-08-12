from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question,interpret_question
def seed(db):
 ps=[(1,'@I1@',1,'Mervyn Neil','Knuckey','Mervyn Neil Knuckey','M','Mervyn Neil /Knuckey/'),(2,'@I2@',2,'Elaine Fay','Cox','Elaine Fay Cox','F','Elaine Fay /Cox/'),(3,'@I3@',3,'Victor Alexander','Knuckey','Victor Alexander Knuckey','M','Victor Alexander /Knuckey/'),(4,'@I4@',4,'Lois Aletha','Waight','Lois Aletha Waight','F','Lois Aletha /Waight/'),(5,'@I5@',5,'Kym Wayne','Knuckey','Kym Wayne Knuckey','M','Kym Wayne /Knuckey/')]
 db.executemany("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",ps)
 for f in (1,2):db.execute("INSERT INTO families(id,gedcom_xref) VALUES(?,?)",(f,f'@F{f}@'))
 for r in [(1,1,'Husband'),(1,2,'Wife'),(1,5,'Child'),(2,3,'Husband'),(2,4,'Wife'),(2,1,'Child')]:db.execute("INSERT INTO family_members VALUES(?,?,?)",r)
 db.commit()
def test_intent_variants():
 assert interpret_question("When was Mervyn born?")=="birth"
 assert interpret_question("What is Mervyn's birth date?")=="birth"
 assert interpret_question("Tell me about Mervyn's birth")=="birth"
 assert interpret_question("Where did Victor marry?")=="marriage_fact"
 assert interpret_question("Who was Victor's wife?")=="spouses"
 assert interpret_question("What evidence supports this?")=="sources"
def test_context_still_wins(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 assert answer_question(db,"Who was Mervyn Knuckey's father?",1)["answer"]=="Mervyn Neil Knuckey’s father: Victor Alexander Knuckey."
def test_natural_spouse_wording(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 assert answer_question(db,"Who was Victor Knuckey's wife?",1)["answer"]=="Victor Alexander Knuckey’s recorded spouse: Lois Aletha Waight."
def test_natural_children_wording(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 assert "Kym Wayne Knuckey" in answer_question(db,"Did Mervyn have any children?",1)["answer"]
def test_birth_missing_is_grounded(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 r=answer_question(db,"When was Mervyn born?",1)
 assert r["status"]=="not-found" and "No birth information" in r["answer"]
def test_unknown_question_is_honest(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 assert answer_question(db,"What was Mervyn's favourite breakfast?",1)["status"]=="unsupported"
