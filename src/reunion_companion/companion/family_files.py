from __future__ import annotations
from pathlib import Path
from datetime import datetime
import hashlib, json, uuid
from .gedcom import parse_gedcom, child, clean_name

SCHEMA='''
CREATE TABLE IF NOT EXISTS companion_family_files(
 id INTEGER PRIMARY KEY,
 workspace_uuid TEXT NOT NULL UNIQUE,
 display_name TEXT NOT NULL,
 source_application TEXT,
 gedcom_path TEXT,
 fingerprint_json TEXT,
 is_default INTEGER NOT NULL DEFAULT 0,
 is_active INTEGER NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS companion_family_imports(
 id INTEGER PRIMARY KEY,
 workspace_id INTEGER NOT NULL REFERENCES companion_family_files(id) ON DELETE CASCADE,
 source_path TEXT NOT NULL,
 imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 fingerprint_json TEXT
);
'''

def ensure_family_files(db):
    db.executescript(SCHEMA)
    row=db.execute('SELECT id FROM companion_family_files ORDER BY id LIMIT 1').fetchone()
    if not row:
        cur=db.execute("SELECT source_path FROM imports ORDER BY id DESC LIMIT 1").fetchone()
        path=cur['source_path'] if cur else None
        fp=json.dumps(gedcom_fingerprint(path)) if path and Path(path).exists() else None
        db.execute('INSERT INTO companion_family_files(workspace_uuid,display_name,source_application,gedcom_path,fingerprint_json,is_default,is_active) VALUES(?,?,?,?,?,1,1)',(str(uuid.uuid4()),'Knuckey Family History','Reunion',path,fp))
    if not db.execute('SELECT 1 FROM companion_family_files WHERE is_active=1').fetchone():
        db.execute('UPDATE companion_family_files SET is_active=1 WHERE id=(SELECT id FROM companion_family_files ORDER BY is_default DESC,id LIMIT 1)')
    # Associate legacy report history with the initial/default Family File and
    # make future report ownership workspace-aware without rebuilding the table.
    try:
        cols={r['name'] for r in db.execute('PRAGMA table_info(companion_publication_history)')}
        if cols and 'workspace_id' not in cols:
            db.execute('ALTER TABLE companion_publication_history ADD COLUMN workspace_id INTEGER')
        active=db.execute('SELECT id FROM companion_family_files WHERE is_active=1 ORDER BY id LIMIT 1').fetchone()
        if active and 'workspace_id' in {r['name'] for r in db.execute('PRAGMA table_info(companion_publication_history)')}:
            db.execute('UPDATE companion_publication_history SET workspace_id=? WHERE workspace_id IS NULL',(active['id'],))
    except Exception:
        pass
    db.commit()

def list_family_files(db):
    ensure_family_files(db)
    return [dict(r) for r in db.execute('SELECT * FROM companion_family_files ORDER BY is_default DESC,display_name')]

def active_family_file(db):
    ensure_family_files(db)
    r=db.execute('SELECT * FROM companion_family_files WHERE is_active=1 ORDER BY id LIMIT 1').fetchone()
    return dict(r) if r else None

def gedcom_fingerprint(path):
    p=Path(path).expanduser().resolve(); roots=parse_gedcom(p)
    people=[]
    for r in roots:
        if r.tag!='INDI' or not r.xref: continue
        nm=child(r,'NAME'); g,s,d=clean_name(nm.value if nm else '')
        birt=child(r,'BIRT'); dt=child(birt,'DATE') if birt else None
        people.append((r.xref,(d or '').casefold(),(dt.value if dt else '').casefold()))
    people.sort()
    anchors=people[:200]
    payload='\n'.join('|'.join(x) for x in anchors)
    return {'people':len(people),'anchors':anchors,'anchor_sha256':hashlib.sha256(payload.encode()).hexdigest()}

def compare_fingerprint(old,new):
    if not old: return {'classification':'unknown','score':0.0,'reason':'No previous fingerprint is available.'}
    if isinstance(old,str): old=json.loads(old)
    oa={tuple(x) for x in old.get('anchors',[])}; na={tuple(x) for x in new.get('anchors',[])}
    score=len(oa&na)/max(1,len(oa|na))
    ratio=min(old.get('people',0),new.get('people',0))/max(1,max(old.get('people',0),new.get('people',0)))
    combined=.8*score+.2*ratio
    if combined>=.70: c='confident_match'
    elif combined>=.35: c='possible_match'
    else: c='likely_different'
    return {'classification':c,'score':round(combined,3),'anchor_overlap':round(score,3),'count_ratio':round(ratio,3)}

def register_family_file(db,name,gedcom_path,source_application='GEDCOM',make_default=False):
    ensure_family_files(db); fp=gedcom_fingerprint(gedcom_path)
    if make_default: db.execute('UPDATE companion_family_files SET is_default=0')
    cur=db.execute('INSERT INTO companion_family_files(workspace_uuid,display_name,source_application,gedcom_path,fingerprint_json,is_default,is_active) VALUES(?,?,?,?,?,?,0)',(str(uuid.uuid4()),name.strip(),source_application.strip() or 'GEDCOM',str(Path(gedcom_path).expanduser().resolve()),json.dumps(fp),1 if make_default else 0))
    db.commit(); return cur.lastrowid

def verify_refresh_for_workspace(db,workspace_id,gedcom_path):
    ensure_family_files(db); row=db.execute('SELECT * FROM companion_family_files WHERE id=?',(workspace_id,)).fetchone()
    if not row: raise ValueError('Unknown Family File.')
    new=gedcom_fingerprint(gedcom_path); cmp=compare_fingerprint(row['fingerprint_json'],new)
    return {'workspace':dict(row),'incoming':new,'match':cmp}

def record_workspace_import(db,workspace_id,path):
    fp=gedcom_fingerprint(path); p=str(Path(path).expanduser().resolve())
    db.execute('UPDATE companion_family_files SET gedcom_path=?,fingerprint_json=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',(p,json.dumps(fp),workspace_id))
    db.execute('INSERT INTO companion_family_imports(workspace_id,source_path,fingerprint_json) VALUES(?,?,?)',(workspace_id,p,json.dumps(fp)))
    db.commit()

def set_active_family(db,workspace_id):
    ensure_family_files(db)
    if not db.execute('SELECT 1 FROM companion_family_files WHERE id=?',(workspace_id,)).fetchone(): raise ValueError('Unknown Family File.')
    db.execute('UPDATE companion_family_files SET is_active=0'); db.execute('UPDATE companion_family_files SET is_active=1 WHERE id=?',(workspace_id,)); db.commit()


def rename_family_file(db,workspace_id,new_name):
    ensure_family_files(db)
    name=(new_name or '').strip()
    if not name: raise ValueError('Family File name cannot be empty.')
    row=db.execute('SELECT id FROM companion_family_files WHERE id=?',(workspace_id,)).fetchone()
    if not row: raise ValueError('Unknown Family File.')
    db.execute('UPDATE companion_family_files SET display_name=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',(name,workspace_id));db.commit()

def set_default_family(db,workspace_id):
    ensure_family_files(db)
    if not db.execute('SELECT 1 FROM companion_family_files WHERE id=?',(workspace_id,)).fetchone(): raise ValueError('Unknown Family File.')
    db.execute('UPDATE companion_family_files SET is_default=0')
    db.execute('UPDATE companion_family_files SET is_default=1,updated_at=CURRENT_TIMESTAMP WHERE id=?',(workspace_id,));db.commit()

def family_report_count(db,workspace_id):
    try:
        cols={r['name'] for r in db.execute('PRAGMA table_info(companion_publication_history)')}
        if 'workspace_id' not in cols:return 0
        return db.execute('SELECT COUNT(*) FROM companion_publication_history WHERE workspace_id=?',(workspace_id,)).fetchone()[0]
    except Exception:return 0

def delete_family_file(db,workspace_id,delete_reports=False):
    ensure_family_files(db)
    rows=list_family_files(db)
    row=next((x for x in rows if x['id']==workspace_id),None)
    if not row: raise ValueError('Unknown Family File.')
    if len(rows)<=1: raise ValueError('The only remaining Family File cannot be deleted.')
    if row.get('is_default'): raise ValueError('Choose another default Family File before deleting this one.')
    if row.get('is_active'): raise ValueError('Switch to another Family File before deleting this one.')
    # Report files are optional destructive cleanup; otherwise retain history as unassigned legacy output.
    try:
        cols={r['name'] for r in db.execute('PRAGMA table_info(companion_publication_history)')}
        if 'workspace_id' in cols:
            report_rows=db.execute('SELECT id,output_path FROM companion_publication_history WHERE workspace_id=?',(workspace_id,)).fetchall()
            if delete_reports:
                from .beta3_publishing import delete_publication
                for r in report_rows: delete_publication(db,r['id'])
            else:
                db.execute('UPDATE companion_publication_history SET workspace_id=NULL WHERE workspace_id=?',(workspace_id,))
    except Exception:
        if delete_reports: raise
    db.execute('DELETE FROM companion_family_imports WHERE workspace_id=?',(workspace_id,))
    db.execute('DELETE FROM companion_family_files WHERE id=?',(workspace_id,));db.commit()
