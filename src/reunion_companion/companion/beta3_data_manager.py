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

def import_history(db,limit=30,offset=0):
    ensure_companion_tables(db)
    out=[]
    for r in db.execute(
        "SELECT * FROM companion_import_history ORDER BY id DESC LIMIT ? OFFSET ?",
        (max(0,int(limit)),max(0,int(offset))),
    ).fetchall():
        d=dict(r);d["counts"]=json.loads(d.pop("counts_json") or "{}");d["diff"]=json.loads(d.pop("diff_json") or "{}");out.append(d)
    return out

def import_history_count(db):
    ensure_companion_tables(db)
    return int(db.execute("SELECT COUNT(*) FROM companion_import_history").fetchone()[0])

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
    # FFD 1.8 Build 1 compatibility wrapper. All imports now use the safe full-refresh engine.
    from .safe_refresh import safe_refresh
    r=safe_refresh(db_path,gedcom_path)
    # Keep the older UI/API keys while exposing the richer change report.
    flat={k: sum(v.get(x,0) for x in ("added","changed","removed")) for k,v in r["changes"].items()}
    return {"source_path":r["source"]["path"],"counts":r["validation"],"diff":flat,"changes":r["changes"],
            "backup_path":r["backup_path"],"validation":r["validation"],"promoted":r["promoted"]}

def reload_current(db_path):
    from .safe_refresh import safe_reload_current
    r=safe_reload_current(db_path)
    flat={k: sum(v.get(x,0) for x in ("added","changed","removed")) for k,v in r["changes"].items()}
    return {"source_path":r["source"]["path"],"counts":r["validation"],"diff":flat,"changes":r["changes"],
            "backup_path":r["backup_path"],"validation":r["validation"],"promoted":r["promoted"]}
