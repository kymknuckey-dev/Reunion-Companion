from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_person_story import _family

def seed(db):
    people=[
      (1,'@I1@',1,'Mervyn','Knuckey','Mervyn Knuckey','M','Mervyn /Knuckey/'),
      (2,'@I2@',2,'Elaine','Cox','Elaine Fay Cox','F','Elaine /Cox/'),
      (3,'@I3@',3,'Kym','Knuckey','Kym Wayne Knuckey','M','Kym /Knuckey/'),
      (4,'@I4@',4,'Jodie','Knuckey','Jodie Karen Knuckey','F','Jodie /Knuckey/'),
      (5,'@I5@',5,'Jamie','Knuckey','Jamie Lee Knuckey','M','Jamie /Knuckey/'),
      (6,'@I6@',6,'Victor','Knuckey','Victor Alexander Knuckey','M','Victor /Knuckey/'),
      (7,'@I7@',7,'Lois','Waight','Lois Aletha Waight','F','Lois /Waight/'),
      (8,'@I8@',8,'Brian','Knuckey','Brian Victor Knuckey','M','Brian /Knuckey/'),
    ]
    db.executemany("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",people)
    for fid in (1,2): db.execute("INSERT INTO families(id,gedcom_xref) VALUES(?,?)",(fid,f'@F{fid}@'))
    for row in [(1,1,'Husband'),(1,2,'Wife'),(1,3,'Child'),(1,4,'Child'),(1,5,'Child'),
                (2,6,'Husband'),(2,7,'Wife'),(2,1,'Child'),(2,8,'Child')]:
        db.execute("INSERT INTO family_members VALUES(?,?,?)",row)
    db.commit()

def rels(db,pid):
    return {(label,name) for _,label,name,_ in _family(db,pid)}

def test_mervyn_relationships(tmp_path):
    db=connect(tmp_path/"x.sqlite3");seed(db);r=rels(db,1)
    assert ("Spouse","Elaine Fay Cox") in r
    assert ("Son","Kym Wayne Knuckey") in r
    assert ("Daughter","Jodie Karen Knuckey") in r
    assert ("Son","Jamie Lee Knuckey") in r
    assert ("Father","Victor Alexander Knuckey") in r
    assert ("Mother","Lois Aletha Waight") in r
    assert ("Brother","Brian Victor Knuckey") in r

def test_not_mislabelled_from_family_role(tmp_path):
    db=connect(tmp_path/"x.sqlite3");seed(db);r=rels(db,1)
    assert ("Spouse","Victor Alexander Knuckey") not in r
    assert ("Child","Brian Victor Knuckey") not in r
    assert ("Spouse","Lois Aletha Waight") not in r

def test_relationships_are_perspective_aware(tmp_path):
    db=connect(tmp_path/"x.sqlite3");seed(db);r=rels(db,8)
    assert ("Father","Victor Alexander Knuckey") in r
    assert ("Mother","Lois Aletha Waight") in r
    assert ("Brother","Mervyn Knuckey") in r
