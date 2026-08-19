from __future__ import annotations
from dataclasses import dataclass,field
from pathlib import Path
from typing import Optional
import re
from .database import reset_imported_data

EVENT_TAGS={"BIRT":"Birth","DEAT":"Death","BURI":"Burial","CREM":"Cremation","OCCU":"Occupation","EDUC":"Education","RELI":"Religion","RESI":"Residence","CHR":"Christening","BAPM":"Baptism","EMIG":"Emigration","IMMI":"Immigration","NATU":"Naturalization","PROB":"Probate","WILL":"Will","CHAN":"Changed"}
NOTE_LABELS={"NOTE":"Note","HEAL":"Medical","HIST":"Research","MILI":"Military","MILS":"Military Service","_MILS":"Military Service"}

@dataclass
class Node:
    level:int; tag:str; value:str=""; xref:Optional[str]=None; children:list["Node"]=field(default_factory=list)

def parse_line(line):
    m=re.match(r"^(\d+)\s+(?:(@[^@]+@)\s+)?([A-Za-z0-9_]+)(?:\s+(.*))?$",line.rstrip())
    if not m: raise ValueError(f"Unparseable GEDCOM line: {line!r}")
    return Node(int(m.group(1)),m.group(3),m.group(4) or "",m.group(2))

def parse_gedcom(path):
    roots=[];stack=[]
    for raw in Path(path).read_text(encoding="utf-8",errors="replace").splitlines():
        if not raw.strip(): continue
        n=parse_line(raw)
        while stack and stack[-1].level>=n.level: stack.pop()
        (stack[-1].children if stack else roots).append(n)
        stack.append(n)
    return roots

def child(n,t): return next((c for c in n.children if c.tag==t),None)
def children(n,t): return [c for c in n.children if c.tag==t]

def reconstruct_text(n):
    text=n.value or ""
    def walk(parent):
        nonlocal text
        for c in parent.children:
            if c.tag=="CONT": text+="\n"+(c.value or "")
            elif c.tag=="CONC": text+=(c.value or "")
            if c.tag in ("CONT","CONC"): walk(c)
    walk(n)
    return text.strip("\n")

def descendants(n):
    for c in n.children:
        yield c
        yield from descendants(c)

def source_nodes(n, prefix=""):
    out=[]
    for c in n.children:
        path=(prefix+"/"+c.tag).strip("/")
        if c.tag=="SOUR" and re.fullmatch(r"@S\d+@",c.value.strip()): out.append((c,c.value.strip(),path))
        out.extend(source_nodes(c,path))
    return out

def source_xrefs(n): return [x for _,x,_ in source_nodes(n)]

def clean_name(raw):
    m=re.search(r"/([^/]*)/",raw or "");surname=m.group(1).strip() if m else ""
    given=re.sub(r"/[^/]*/","",raw or "").strip()
    return given,surname," ".join((given+" "+surname).split())

def note_label(tag):
    return NOTE_LABELS.get(tag,tag.lstrip("_").replace("_"," ").title() if tag.startswith("_") else tag)

def is_nxref(v): return bool(re.fullmatch(r"@N\d+@",(v or "").strip()))

def media_payload(n):
    f=child(n,"FILE")
    if not f:return None
    title=child(n,"TITL");typ=child(n,"_TYPE") or child(n,"FORM");prim=child(n,"_PRIM")
    preferred=1 if prim and (prim.value or "").strip().upper()=="Y" else 0
    return f.value.strip(),(title.value.strip() if title else Path(f.value.strip()).name),(typ.value.strip() if typ else None),preferred

def import_gedcom(db,path):
    p=Path(path).expanduser();roots=parse_gedcom(p);reset_imported_data(db)
    top_notes={r.xref:r for r in roots if r.tag=="NOTE" and r.xref}
    top_sources={r.xref:r for r in roots if r.tag=="SOUR" and r.xref}
    indis=[r for r in roots if r.tag=="INDI" and r.xref]
    fams=[r for r in roots if r.tag=="FAM" and r.xref]

    source_ids={}
    for s in top_sources.values():
        tit=child(s,"TITL");txt=child(s,"TEXT");typ=child(s,"TYPE")
        title=reconstruct_text(tit) if tit else None
        text=reconstruct_text(txt) if txt else None
        source_type=reconstruct_text(typ) if typ else None
        display=text or title or source_type or s.xref
        sid=db.execute("INSERT INTO sources(gedcom_xref,title,text,source_type,display_text) VALUES(?,?,?,?,?)",(s.xref,title,text,source_type,display)).lastrowid
        source_ids[s.xref]=sid

    pids={}
    for r in indis:
        nm=child(r,"NAME");g,s,d=clean_name(nm.value if nm else "");sex=child(r,"SEX")
        pid=db.execute("INSERT INTO people(gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?)",(r.xref,int(re.sub(r"\D","",r.xref) or 0),g,s,d or r.xref,sex.value if sex else None,nm.value if nm else None)).lastrowid
        pids[r.xref]=pid

    fids={}
    for f in fams:
        marr=child(f,"MARR");md=child(marr,"DATE") if marr else None;mp=child(marr,"PLAC") if marr else None
        fid=db.execute("INSERT INTO families(gedcom_xref,marriage_date,marriage_place) VALUES(?,?,?)",(f.xref,md.value if md else None,mp.value if mp else None)).lastrowid
        fids[f.xref]=fid
        for tag,role in (("HUSB","Husband"),("WIFE","Wife"),("CHIL","Child")):
            for x in children(f,tag):
                if x.value in pids: db.execute("INSERT OR IGNORE INTO family_members VALUES(?,?,?)",(fid,pids[x.value],role))

    def add_citation(source_xref,scope,owner_xref=None,person_id=None,family_id=None,event_id=None,note_id=None,context_tag=None,context_path=None):
        sid=source_ids.get(source_xref)
        if not sid:return
        db.execute("INSERT INTO citations(source_id,owner_scope,person_id,family_id,event_id,note_id,gedcom_owner_xref,context_tag,context_path) VALUES(?,?,?,?,?,?,?,?,?)",(sid,scope,person_id,family_id,event_id,note_id,owner_xref,context_tag,context_path))

    def add_note(pid,origin,nr,xref=None,referenced=False):
        nid=db.execute("INSERT INTO notes(person_id,note_type,gedcom_tag,gedcom_note_xref,text,is_referenced) VALUES(?,?,?,?,?,?)",(pid,note_label(origin),origin,xref,reconstruct_text(nr),1 if referenced else 0)).lastrowid
        for sn,sx,pathx in source_nodes(nr):
            if sx in source_ids:
                db.execute("INSERT OR IGNORE INTO note_sources VALUES(?,?,?)",(nid,source_ids[sx],"GEDCOM"))
                add_citation(sx,"note",owner_xref=xref,person_id=pid,note_id=nid,context_tag=origin,context_path=pathx)
        return nid

    media_keys={}
    for r in indis:
        pid=pids[r.xref]
        consumed_source_node_ids=set()
        for c in r.children:
            if c.tag in EVENT_TAGS:
                dt=child(c,"DATE");pl=child(c,"PLAC");nt=child(c,"NOTE")
                eid=db.execute("INSERT INTO events(person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(?,?,?,?,?,?,?)",(pid,EVENT_TAGS[c.tag],dt.value if dt else None,pl.value if pl else None,(c.value or None) if c.value!="Y" else None,reconstruct_text(nt) if nt and not is_nxref(nt.value) else None,c.tag)).lastrowid
                for sn,sx,pathx in source_nodes(c):
                    if sx in source_ids:
                        db.execute("INSERT OR IGNORE INTO event_sources VALUES(?,?,?)",(eid,source_ids[sx],"GEDCOM"))
                        add_citation(sx,"event",owner_xref=r.xref,person_id=pid,event_id=eid,context_tag=c.tag,context_path=pathx)
                        consumed_source_node_ids.add(id(sn))
                for ob in children(c,"OBJE"):
                    mp=media_payload(ob)
                    if mp:
                        fp,title,typ,preferred=mp;resolved=str(Path(fp).expanduser());key=("event",fp,title)
                        mid=media_keys.get(key)
                        if not mid:
                            mid=db.execute("INSERT INTO media(file_path,title,media_type,exists_on_disk,attachment_scope,attachment_label,is_preferred) VALUES(?,?,?,?,?,?,?)",(resolved,title,typ,int(Path(resolved).exists()),"event",EVENT_TAGS[c.tag],preferred)).lastrowid;media_keys[key]=mid
                        db.execute("INSERT OR IGNORE INTO event_media VALUES(?,?,?)",(eid,mid,"GEDCOM"))

            if is_nxref(c.value):
                nr=top_notes.get(c.value.strip())
                if nr: add_note(pid,c.tag,nr,c.value.strip(),True)
            elif c.tag=="NOTE" and c.value:
                add_note(pid,"NOTE",c,None,False)

            if c.tag=="SOUR" and c.value in source_ids:
                db.execute("INSERT OR IGNORE INTO person_sources VALUES(?,?,?)",(pid,source_ids[c.value],"GEDCOM"))
                add_citation(c.value,"person",owner_xref=r.xref,person_id=pid,context_tag="INDI",context_path="SOUR")
                consumed_source_node_ids.add(id(c))

            if c.tag=="OBJE":
                mp=media_payload(c)
                if mp:
                    fp,title,typ,preferred=mp;resolved=str(Path(fp).expanduser());key=("person",fp,title)
                    mid=media_keys.get(key)
                    if not mid:
                        mid=db.execute("INSERT INTO media(file_path,title,media_type,exists_on_disk,attachment_scope,attachment_label,is_preferred) VALUES(?,?,?,?,?,?,?)",(resolved,title,typ,int(Path(resolved).exists()),"person",None,preferred)).lastrowid;media_keys[key]=mid
                    db.execute("INSERT OR IGNORE INTO person_media VALUES(?,?,?)",(pid,mid,"GEDCOM"))

        # Catch citations under non-event person fields (for example NAME, custom fields, etc.).
        for sn,sx,pathx in source_nodes(r):
            if id(sn) in consumed_source_node_ids or sx not in source_ids: continue
            db.execute("INSERT OR IGNORE INTO person_sources VALUES(?,?,?)",(pid,source_ids[sx],"GEDCOM"))
            add_citation(sx,"person",owner_xref=r.xref,person_id=pid,context_tag=pathx.split('/')[0] if pathx else "INDI",context_path=pathx)

    for f in fams:
        fid=fids[f.xref]
        for sn,sx,pathx in source_nodes(f):
            if sx in source_ids:
                db.execute("INSERT OR IGNORE INTO family_sources VALUES(?,?,?)",(fid,source_ids[sx],"GEDCOM"))
                add_citation(sx,"family",owner_xref=f.xref,family_id=fid,context_tag=pathx.split('/')[0] if pathx else "FAM",context_path=pathx)
        for ob in children(f,"OBJE"):
            mp=media_payload(ob)
            if mp:
                fp,title,typ,preferred=mp;resolved=str(Path(fp).expanduser());key=("family",fp,title)
                mid=media_keys.get(key)
                if not mid:
                    mid=db.execute("INSERT INTO media(file_path,title,media_type,exists_on_disk,attachment_scope,attachment_label,is_preferred) VALUES(?,?,?,?,?,?,?)",(resolved,title,typ,int(Path(resolved).exists()),"family","Marriage",preferred)).lastrowid;media_keys[key]=mid
                db.execute("INSERT OR IGNORE INTO family_media VALUES(?,?,?)",(fid,mid,"GEDCOM"))

        # Reunion may attach media specifically beneath the family MARR event
        # (FAM -> MARR -> OBJE -> FILE). Preserve that semantic context while
        # still linking the media to the family so publishing can surface it.
        marr=child(f,"MARR")
        if marr:
            for ob in children(marr,"OBJE"):
                mp=media_payload(ob)
                if mp:
                    fp,title,typ,preferred=mp;resolved=str(Path(fp).expanduser());key=("family-marriage",fp,title)
                    mid=media_keys.get(key)
                    if not mid:
                        mid=db.execute("INSERT INTO media(file_path,title,media_type,exists_on_disk,attachment_scope,attachment_label,is_preferred) VALUES(?,?,?,?,?,?,?)",(resolved,title,typ,int(Path(resolved).exists()),"family-event","Marriage",preferred)).lastrowid;media_keys[key]=mid
                    db.execute("INSERT OR IGNORE INTO family_media VALUES(?,?,?)",(fid,mid,"GEDCOM"))

    db.execute("INSERT INTO imports(source_path,source_type) VALUES(?,?)",(str(p),"GEDCOM"));db.commit()
    from .discovery import rebuild_discovery_index
    rebuild_discovery_index(db)
    keys=("people","families","events","notes","media","person_media","event_media","family_media","sources","person_sources","event_sources","note_sources","family_sources","citations")
    return {k:db.execute(f"SELECT COUNT(*) FROM {k}").fetchone()[0] for k in keys}
