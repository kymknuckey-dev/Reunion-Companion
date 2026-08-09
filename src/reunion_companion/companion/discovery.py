from collections import deque
from pathlib import Path

def rebuild_discovery_index(db):
    db.execute("DELETE FROM discovery_fts")
    for p in db.execute("SELECT id,display_name,given_names,surname,sex FROM people"):
        body=" ".join(x for x in (p["display_name"],p["given_names"],p["surname"],p["sex"]) if x)
        db.execute("INSERT INTO discovery_fts VALUES(?,?,?,?,?)",("person",p["id"],p["id"],p["display_name"],body))
    for e in db.execute("SELECT id,person_id,event_type,date_text,place_text,value_text,note_text FROM events"):
        body=" ".join(x for x in (e["event_type"],e["date_text"],e["place_text"],e["value_text"],e["note_text"]) if x)
        db.execute("INSERT INTO discovery_fts VALUES(?,?,?,?,?)",("event",e["id"],e["person_id"],e["event_type"],body))
    for n in db.execute("SELECT id,person_id,note_type,text FROM notes"):
        db.execute("INSERT INTO discovery_fts VALUES(?,?,?,?,?)",("note",n["id"],n["person_id"],n["note_type"],n["text"]))
    for m in db.execute("""SELECT m.id,m.title,m.file_path,m.attachment_label,COALESCE(pm.person_id,e.person_id,ff.person_id) person_id
                           FROM media m LEFT JOIN person_media pm ON pm.media_id=m.id
                           LEFT JOIN event_media em ON em.media_id=m.id LEFT JOIN events e ON e.id=em.event_id
                           LEFT JOIN family_media fm ON fm.media_id=m.id LEFT JOIN family_members ff ON ff.family_id=fm.family_id"""):
        body=" ".join(x for x in (m["title"],m["file_path"],m["attachment_label"]) if x)
        db.execute("INSERT INTO discovery_fts VALUES(?,?,?,?,?)",("media",m["id"],m["person_id"],m["title"] or Path(m["file_path"]).name,body))
    for s in db.execute("SELECT id,gedcom_xref,display_text,source_type,text,title FROM sources"):
        title=s["display_text"] or s["title"] or s["gedcom_xref"]
        body=" ".join(x for x in (s["display_text"],s["source_type"],s["text"],s["title"]) if x)
        db.execute("INSERT INTO discovery_fts VALUES(?,?,?,?,?)",("source",s["id"],None,title,body))
    db.commit()

def cross_search(db,text,limit=100):
    q=' '.join(f'"{w.replace(chr(34),"")}"' for w in text.split())
    return db.execute("SELECT kind,object_id,person_id,title,snippet(discovery_fts,4,'[',']',' … ',12) snippet FROM discovery_fts WHERE discovery_fts MATCH ? LIMIT ?",(q,limit)).fetchall()
def place_search(db,text,limit=200):
    q=f'%{text}%'; return db.execute("SELECT p.id person_id,p.display_name,e.event_type,e.date_text,e.place_text FROM events e JOIN people p ON p.id=e.person_id WHERE COALESCE(e.place_text,'') LIKE ? ORDER BY e.place_text,p.display_name LIMIT ?",(q,limit)).fetchall()
def family_snapshot(db,pid):
    out=[]
    for f in db.execute('SELECT f.*,fm.role FROM families f JOIN family_members fm ON fm.family_id=f.id WHERE fm.person_id=? ORDER BY f.id',(pid,)):
        mem=db.execute('SELECT p.id,p.display_name,fm.role FROM family_members fm JOIN people p ON p.id=fm.person_id WHERE fm.family_id=? ORDER BY fm.role,p.display_name',(f['id'],)).fetchall(); out.append((f,mem))
    return out
def relationship_connections(db,pid):
    ps=[];ss=[];cs=[];sibs=[]
    for f,m in family_snapshot(db,pid):
        role=next((x['role'] for x in m if x['id']==pid),None)
        for x in m:
            if x['id']==pid: continue
            if role=='Child': (ps if x['role'] in ('Husband','Wife') else sibs if x['role']=='Child' else []).append(x)
            elif role in ('Husband','Wife'): (cs if x['role']=='Child' else ss if x['role'] in ('Husband','Wife') else []).append(x)
    def d(xs):
        seen=set();o=[]
        for x in xs:
            if x['id'] not in seen: seen.add(x['id']);o.append(x)
        return o
    return {'parents':d(ps),'spouses':d(ss),'children':d(cs),'siblings':d(sibs)}
def _walk(db,pid,key,generations):
    out=[];q=deque([(pid,0)]);seen={pid}
    while q:
        cur,g=q.popleft()
        if g>=generations: continue
        for x in relationship_connections(db,cur)[key]:
            if x['id'] in seen: continue
            seen.add(x['id']);out.append((g+1,x));q.append((x['id'],g+1))
    return out
def ancestors(db,pid,generations=5): return _walk(db,pid,'parents',generations)
def descendants(db,pid,generations=5): return _walk(db,pid,'children',generations)
def research_gaps(db,pid):
    ets={r['event_type'] for r in db.execute('SELECT event_type FROM events WHERE person_id=?',(pid,))}; gaps=[]
    for t in ('Birth','Death','Burial'):
        if t not in ets:gaps.append((t,'No event recorded'))
    if 'Occupation' not in ets:gaps.append(('Occupation','No occupation recorded'))
    mc=db.execute('SELECT COUNT(*) FROM person_media WHERE person_id=?',(pid,)).fetchone()[0]
    if mc==0:gaps.append(('Person media','No directly linked person media'))
    sc=db.execute('SELECT COUNT(*) FROM person_sources WHERE person_id=?',(pid,)).fetchone()[0]
    if sc==0:gaps.append(('Sources','No directly linked source records'))
    return gaps
def duplicate_people(db,limit=100): return db.execute('SELECT display_name,COUNT(*) count,GROUP_CONCAT(id) ids FROM people GROUP BY lower(trim(display_name)) HAVING COUNT(*)>1 ORDER BY count DESC,display_name LIMIT ?',(limit,)).fetchall()
def duplicate_media(db,limit=100): return db.execute('SELECT MIN(file_path) file_path,COUNT(*) count,GROUP_CONCAT(id) ids FROM media GROUP BY lower(file_path) HAVING COUNT(*)>1 ORDER BY count DESC,file_path LIMIT ?',(limit,)).fetchall()
def person_evidence_summary(db,pid):
    p=db.execute('SELECT * FROM people WHERE id=?',(pid,)).fetchone();
    if not p:return None
    ev=db.execute('SELECT * FROM events WHERE person_id=? ORDER BY id',(pid,)).fetchall(); notes=db.execute('SELECT * FROM notes WHERE person_id=? ORDER BY id',(pid,)).fetchall(); c=relationship_connections(db,pid)
    media=db.execute("SELECT m.* FROM media m JOIN person_media pm ON pm.media_id=m.id WHERE pm.person_id=? UNION SELECT m.* FROM media m JOIN event_media em ON em.media_id=m.id JOIN events e ON e.id=em.event_id WHERE e.person_id=?",(pid,pid)).fetchall()
    return {'person':p,'events':ev,'notes':notes,'connections':c,'media':media,'gaps':research_gaps(db,pid)}
