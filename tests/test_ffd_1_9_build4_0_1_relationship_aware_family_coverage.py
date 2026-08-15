from reunion_companion.companion.database import connect
from reunion_companion.companion.person_narrative import person_narrative, NARRATIVE_VERSION
from reunion_companion.companion.version_identity import FFD_BUILD, RELEASE_TAG

class Client:
    def __init__(self,text): self.text=text
    def generate(self,prompt): return self.text

def seed_mervyn(db):
    db.execute("INSERT INTO people(id,display_name,sex) VALUES(1,'Mervyn Neil Knuckey','M'),(2,'Elaine Fay Cox','F'),(3,'Kym Wayne Knuckey','M'),(4,'Jodie Karen Knuckey','F'),(5,'Jamie Lee Knuckey','M')")
    db.execute("INSERT INTO families(id,marriage_date,marriage_place) VALUES(98,'21 JAN 1961','Reynella Uniting Church, Reynella, South Australia.')")
    db.executemany("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,?)",[(98,1,'Husband'),(98,2,'Wife'),(98,3,'Child'),(98,4,'Child'),(98,5,'Child')])
    db.execute("INSERT INTO notes(id,person_id,note_type,text) VALUES(1,1,'Misc','Recorded life narrative.')")
    db.commit()

def test_jamie_elsewhere_does_not_count_as_complete_family_coverage(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed_mervyn(db)
    prose=("Mervyn Neil Knuckey married Elaine Fay Cox on 21 JAN 1961 at Reynella Uniting Church, Reynella, South Australia.\n\n"
           "They later settled into a leased residence owned by their son, Jamie Lee Knuckey.")
    out=person_narrative(db,1,client=Client(prose),force=True)["narrative"]
    assert "They had 3 children: Kym Wayne Knuckey, Jodie Karen Knuckey, and Jamie Lee Knuckey." in out
    assert "owned by their son, Jamie Lee Knuckey" in out

def test_complete_family_passage_is_not_duplicated(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed_mervyn(db)
    prose=("Mervyn Neil Knuckey married Elaine Fay Cox on 21 JAN 1961. "
           "They had three children: Kym Wayne Knuckey, Jodie Karen Knuckey, and Jamie Lee Knuckey.")
    out=person_narrative(db,1,client=Client(prose),force=True)["narrative"]
    assert out==prose

def test_release_identity():
    assert FFD_BUILD
    assert RELEASE_TAG.startswith("ffd-1.9-")
    assert NARRATIVE_VERSION=="ffd-1.9-build-4.0.1-v1"
