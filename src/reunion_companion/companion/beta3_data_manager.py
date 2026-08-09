from pathlib import Path
from datetime import datetime
import hashlib,json,os,sqlite3,tempfile
from .database import connect
from .gedcom import import_gedcom

SCHEMA="""
CREATE TABLE IF NOT EXISTS companion_import_history(
 id INTEGER PRIMARY KEY, source_path TEXT NOT NULL, imported_at TEXT NOT NULL,
 source_size INTEGER, source_mtime REAL, source_sha256 TEXT,
 counts_json TEXT NOT NULL, diff_json TEXT, status TEXT NOT NULL DEFAULT 'success');
CREATE TABLE IF NOT EXISTS companion_publication_history(
 id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, kind TEXT NOT NULL,
 subject TEXT, output_path TEXT NOT NULL, output_format TEXT NOT NULL);
"""
COUNT_TABLES=("people","families","events","notes","sources","media","citations")

def ensure_companion_tables(db):
    db.executescript(SCHEMA); db.commit()

def dataset_counts(db):
    out={}
    for x in COUNT_TABLES:
        try: out[x]=db.execute(f"SELECT COUNT(*) FROM {x}").fetchone()[0]
        except sqlite3.DatabaseError: out[x]=0
    return out

def _sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def current_gedcom(db):
    ensure_companion_tables(db)
    r=db.execute("SELECT source_path,imported_at FROM imports ORDER BY id DESC LIMIT 1").fetchone()
    if r:return dict(r)
    r=db.execute("SELECT source_path,imported_at FROM companion_import_history WHERE status IN ('success','baseline') ORDER BY id DESC LIMIT 1").fetchone()
    return dict(r) if r else None

def import_history(db,limit=30):
    ensure_companion_tables(db)
    out=[]
    for r in db.execute("SELECT * FROM companion_import_history ORDER BY id DESC LIMIT ?",(limit,)).fetchall():
        d=dict(r);d["counts"]=json.loads(d.pop("counts_json") or "{}");d["diff"]=json.loads(d.pop("diff_json") or "{}");out.append(d)
    return out

def _diff(a,b):return {k:b.get(k,0)-a.get(k,0) for k in sorted(set(a)|set(b))}

def seed_history_from_current(db):
    ensure_companion_tables(db)
    if db.execute("SELECT COUNT(*) FROM companion_import_history").fetchone()[0]:return
    cur=current_gedcom(db)
    if not cur:return
    p=Path(cur["source_path"]).expanduser();counts=dataset_counts(db)
    db.execute("""INSERT INTO companion_import_history
      (source_path,imported_at,source_size,source_mtime,source_sha256,counts_json,diff_json,status)
      VALUES(?,?,?,?,?,?,?,?)""",
      (str(p),cur["imported_at"],p.stat().st_size if p.exists() else None,p.stat().st_mtime if p.exists() else None,
       _sha(p) if p.exists() else None,json.dumps(counts),json.dumps({}),"baseline"));db.commit()

def staged_import(db_path,gedcom_path):
    db_path=Path(db_path).expanduser().resolve();ged=Path(gedcom_path).expanduser().resolve()
    if not ged.is_file():raise FileNotFoundError(str(ged))
    src=connect(db_path);ensure_companion_tables(src);seed_history_from_current(src);before=dataset_counts(src)
    fd,tmpname=tempfile.mkstemp(prefix="reunion-companion-stage-",suffix=".sqlite3",dir=str(db_path.parent));os.close(fd);tmp=Path(tmpname)
    try:
        clone=sqlite3.connect(tmp);src.backup(clone);clone.close();src.close()
        work=connect(tmp);ensure_companion_tables(work)
        result=import_gedcom(work,ged);after=dataset_counts(work);stat=ged.stat();now=datetime.now().isoformat(timespec="seconds")
        work.execute("""INSERT INTO companion_import_history
          (source_path,imported_at,source_size,source_mtime,source_sha256,counts_json,diff_json,status)
          VALUES(?,?,?,?,?,?,?,?)""",
          (str(ged),now,stat.st_size,stat.st_mtime,_sha(ged),json.dumps(after),json.dumps(_diff(before,after)),"success"))
        work.commit();work.close();os.replace(tmp,db_path)
        return {"source_path":str(ged),"counts":after,"diff":_diff(before,after),"import_result":result}
    except Exception:
        try:src.close()
        except Exception:pass
        if tmp.exists():tmp.unlink()
        raise

def reload_current(db_path):
    db=connect(db_path)
    try:cur=current_gedcom(db)
    finally:db.close()
    if not cur:raise RuntimeError("No current GEDCOM is recorded.")
    return staged_import(db_path,cur["source_path"])
