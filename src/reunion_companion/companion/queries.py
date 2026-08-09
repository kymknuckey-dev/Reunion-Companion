def stats(db):
    return {t:db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("people","families","events","notes","media","person_media","event_media","family_media","sources")}

def search_people(db,text,limit=50):
    q=f"%{text}%"
    return db.execute("SELECT id,gedcom_xref,reunion_person_id,display_name,sex FROM people WHERE display_name LIKE ? OR given_names LIKE ? OR surname LIKE ? ORDER BY surname,given_names LIMIT ?",(q,q,q,limit)).fetchall()

def resolve_person(db,token):
    token=token.strip()
    if token.startswith("@") and token.endswith("@"):
        r=db.execute("SELECT id FROM people WHERE gedcom_xref=?",(token,)).fetchone(); return [r["id"]] if r else []
    if token.isdigit():
        r=db.execute("SELECT id FROM people WHERE id=?",(int(token),)).fetchone(); return [r["id"]] if r else []
    return [r["id"] for r in search_people(db,token,20)]

def get_person(db,pid):
    p=db.execute("SELECT * FROM people WHERE id=?",(pid,)).fetchone()
    if not p:return None
    events=db.execute("SELECT * FROM events WHERE person_id=? ORDER BY id",(pid,)).fetchall()
    notes=db.execute("SELECT * FROM notes WHERE person_id=? ORDER BY id",(pid,)).fetchall()
    pm=db.execute("SELECT m.*,pm.relation,'Person' attached_to FROM media m JOIN person_media pm ON pm.media_id=m.id WHERE pm.person_id=? ORDER BY COALESCE(m.title,m.file_path)",(pid,)).fetchall()
    em=db.execute("SELECT m.*,em.relation,e.event_type attached_to,e.date_text,e.place_text FROM media m JOIN event_media em ON em.media_id=m.id JOIN events e ON e.id=em.event_id WHERE e.person_id=? ORDER BY e.id",(pid,)).fetchall()
    fams=db.execute("SELECT f.id,f.gedcom_xref,fm.role,f.marriage_date,f.marriage_place FROM families f JOIN family_members fm ON fm.family_id=f.id WHERE fm.person_id=? ORDER BY f.id",(pid,)).fetchall()
    rels=[]
    for fam in fams:
        members=db.execute("SELECT p.id,p.display_name,fm.role FROM family_members fm JOIN people p ON p.id=fm.person_id WHERE fm.family_id=? ORDER BY fm.role,p.display_name",(fam["id"],)).fetchall()
        rels.append({"family":fam,"members":members})
    fm=db.execute("SELECT DISTINCT m.*,fm.relation,'Marriage' attached_to,f.marriage_date,f.marriage_place FROM media m JOIN family_media fm ON fm.media_id=m.id JOIN families f ON f.id=fm.family_id JOIN family_members ff ON ff.family_id=f.id WHERE ff.person_id=?",(pid,)).fetchall()
    return {"person":p,"events":events,"notes":notes,"person_media":pm,"event_media":em,"family_media":fm,"relationships":rels}

def media_health(db):
    total=db.execute("SELECT COUNT(*) FROM media").fetchone()[0]
    missing=db.execute("SELECT COUNT(*) FROM media WHERE exists_on_disk=0").fetchone()[0]
    return {"total":total,"existing":total-missing,"missing":missing,"person_links":db.execute("SELECT COUNT(*) FROM person_media").fetchone()[0],"event_links":db.execute("SELECT COUNT(*) FROM event_media").fetchone()[0],"family_links":db.execute("SELECT COUNT(*) FROM family_media").fetchone()[0],"legacy_pict":db.execute("SELECT COUNT(*) FROM media WHERE lower(file_path) LIKE '%.pict' OR lower(file_path) LIKE '%.pct'").fetchone()[0]}

def media_search(db,text="",missing_only=False,limit=300):
    clauses=[];args=[]
    if text: clauses.append("(COALESCE(title,'') LIKE ? OR file_path LIKE ? OR COALESCE(attachment_label,'') LIKE ?)");args += [f"%{text}%"]*3
    if missing_only: clauses.append("exists_on_disk=0")
    where=(" WHERE "+" AND ".join(clauses)) if clauses else ""
    args.append(limit)
    return db.execute(f"SELECT id,title,file_path,exists_on_disk,attachment_scope,attachment_label FROM media{where} ORDER BY COALESCE(title,file_path) LIMIT ?",args).fetchall()

def find_by_event(db,event_type,text=None,limit=100):
    if text:
        q=f"%{text}%"
        return db.execute("SELECT p.id,p.display_name,e.event_type,e.date_text,e.place_text,e.value_text FROM events e JOIN people p ON p.id=e.person_id WHERE e.event_type=? AND (COALESCE(e.place_text,'') LIKE ? OR COALESCE(e.date_text,'') LIKE ? OR COALESCE(e.value_text,'') LIKE ?) ORDER BY p.display_name LIMIT ?",(event_type,q,q,q,limit)).fetchall()
    return db.execute("SELECT p.id,p.display_name,e.event_type,e.date_text,e.place_text,e.value_text FROM events e JOIN people p ON p.id=e.person_id WHERE e.event_type=? ORDER BY p.display_name LIMIT ?",(event_type,limit)).fetchall()
