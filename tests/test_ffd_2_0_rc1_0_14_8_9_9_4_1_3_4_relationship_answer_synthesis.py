from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question


def add_person(db, pid, name, sex="U"):
    bits=name.split()
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (pid, f"@I{pid}@", pid, " ".join(bits[:-1]), bits[-1], name, sex, name),
    )


def add_family(db, fid, spouses=(), children=()):
    db.execute("INSERT INTO families(id) VALUES(?)", (fid,))
    for pid, role in spouses:
        db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,?)", (fid, pid, role))
    for pid in children:
        db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,?)", (fid, pid, "child"))


def test_internal_marriage_path_is_synthesised_not_dumped(tmp_path):
    db=connect(tmp_path / "x.db")
    add_person(db, 1, "John Bickle", "M")
    add_person(db, 2, "Richard Bickle", "M")
    add_person(db, 3, "Ann Bickle", "F")
    add_person(db, 4, "William Knuckey", "M")
    add_person(db, 5, "Brian Knuckey", "M")
    add_family(db, 1, spouses=((2, "husband"),), children=(1, 3))
    add_family(db, 2, spouses=((4, "husband"), (3, "wife")))
    add_family(db, 3, spouses=((4, "husband"),), children=(5,))
    db.commit()

    r=answer_question(db, "how is John Bickle related to Brian Knuckey", global_identity_discovery=True)

    assert r["status"] == "ok"
    assert r["kind"] == "connection"
    assert "by marriage through Ann Bickle and William Knuckey" in r["answer"]
    assert "Ann Bickle is John Bickle’s sister" in r["answer"]
    assert "William Knuckey, Ann Bickle’s husband, is Brian Knuckey’s father" in r["answer"]
    assert ";" not in r["answer"]
    assert "is the parent of" not in r["answer"]
    assert "is the child of" not in r["answer"]


def test_selected_duplicate_name_resolves_relationship_search_ambiguity(tmp_path):
    db=connect(tmp_path / "x.db")
    add_person(db, 1, "Susan Lee Jones", "F")
    add_person(db, 2, "Brian Victor Knuckey", "M")
    add_person(db, 3, "Brian Victor Knuckey", "M")
    add_family(db, 1, spouses=((2, "husband"),), children=(1,))
    db.commit()

    first=answer_question(
        db,
        "how is Susan Lee Jones related to Brian Victor Knuckey",
        global_identity_discovery=True,
    )
    assert first["kind"] == "identity-choice"

    chosen=answer_question(
        db,
        "how is Susan Lee Jones related to Brian Victor Knuckey",
        selected_identity_id=2,
        global_identity_discovery=True,
    )
    assert chosen["status"] == "ok"
    assert chosen["kind"] == "relationship"
    assert chosen["from"]["id"] == 1
    assert chosen["to"]["id"] == 2
    assert "Brian Victor Knuckey is Susan Lee Jones’s father" in chosen["answer"]
