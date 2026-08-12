from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_family_chart import family_chart
def seed(db):
 people=[(1,'@I1@',1,'Mervyn','Knuckey','Mervyn Knuckey','M','Mervyn /Knuckey/'),(2,'@I2@',2,'Elaine','Cox','Elaine Cox','F','Elaine /Cox/'),(3,'@I3@',3,'Victor','Knuckey','Victor Knuckey','M','Victor /Knuckey/'),(4,'@I4@',4,'Lois','Waight','Lois Waight','F','Lois /Waight/'),(7,'@I7@',7,'Kym','Knuckey','Kym Knuckey','M','Kym /Knuckey/')]
 db.executemany("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",people)
 for fid in (1,2):db.execute("INSERT INTO families(id,gedcom_xref) VALUES(?,?)",(fid,f'@F{fid}@'))
 for r in [(1,1,'Husband'),(1,2,'Wife'),(1,7,'Child'),(2,3,'Husband'),(2,4,'Wife'),(2,1,'Child')]:db.execute("INSERT INTO family_members VALUES(?,?,?)",r)
 db.commit()
def test_build1_engine_contract_retained(tmp_path):
 db=connect(tmp_path/"x.sqlite3");seed(db);c=family_chart(db,1)
 assert c["selected"]["display_name"]=="Mervyn Knuckey"
 assert {"Victor Knuckey","Lois Waight"}<={n["display_name"] for n in c["ancestors"]}
 assert "Kym Knuckey" in {n["display_name"] for n in c["descendants"]}
