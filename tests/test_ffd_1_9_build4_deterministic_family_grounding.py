from reunion_companion.companion.database import connect
from reunion_companion.companion.person_narrative import person_narrative, source_fingerprint, NARRATIVE_VERSION
from reunion_companion.companion.version_identity import FFD_BUILD, RELEASE_TAG

class Client:
    def __init__(self,text): self.text=text
    def generate(self,prompt): self.prompt=prompt; return self.text

def seed(db):
    db.execute("INSERT INTO people(id,display_name,sex) VALUES(1,'Victor Alexander Knuckey','M'),(2,'Lois Aletha Waight','F'),(3,'Mervyn Neil Knuckey','M'),(4,'Brian Victor Knuckey','M')")
    db.execute("INSERT INTO families(id,marriage_date,marriage_place) VALUES(98,'17 DEC 1927','Stow Memorial Church, Adelaide, South Australia.')")
    db.executemany("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,?)",[(98,1,'Husband'),(98,2,'Wife'),(98,3,'Child'),(98,4,'Child')])
    db.execute("INSERT INTO notes(id,person_id,note_type,text) VALUES(1,1,'Misc','Marriage Certificate, witnessed by J.Reed & C.J.Calder.')")
    db.commit()

def test_llm_receives_authoritative_complete_family(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db)
    c=Client("Victor married Lois Aletha Waight in 1927. They had two children: Mervyn Neil Knuckey and Brian Victor Knuckey.")
    out=person_narrative(db,1,client=c,force=True)["narrative"]
    assert out==c.text
    assert "children of this family: Mervyn Neil Knuckey, Brian Victor Knuckey" in c.prompt
    assert "authoritative" in c.prompt

def test_missing_children_are_deterministically_added_without_repeating_marriage(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db)
    out=person_narrative(db,1,client=Client("Victor married Lois Aletha Waight in 1927."),force=True)["narrative"]
    assert out.count("Lois Aletha Waight")==1
    assert "Mervyn Neil Knuckey" in out and "Brian Victor Knuckey" in out
    assert "grandson" not in out.casefold()

def test_missing_family_is_inserted_from_reunion_structure(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db)
    out=person_narrative(db,1,client=Client("Victor worked in several occupations.\n\nHe later lived in Adelaide."),force=True)["narrative"]
    assert "Victor Alexander Knuckey married Lois Aletha Waight on 17 DEC 1927" in out
    assert "Mervyn Neil Knuckey" in out and "Brian Victor Knuckey" in out

def test_family_changes_invalidate_cache_fingerprint(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db); a=source_fingerprint(db,1)
    db.execute("UPDATE families SET marriage_place='Another place' WHERE id=98");db.commit()
    assert source_fingerprint(db,1)!=a

def test_release_identity():
    assert FFD_BUILD
    assert RELEASE_TAG == f"ffd-1.9-build-{FFD_BUILD}"
    assert NARRATIVE_VERSION.startswith("ffd-1.9-build-")
