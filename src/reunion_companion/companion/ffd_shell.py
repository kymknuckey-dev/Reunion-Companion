from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import re

DEFAULT_SETTINGS={
    "family_title":"Knuckey Family History",
    "research_credit":"Mervyn Neil Knuckey",
    "presentation_mode":False,
    "recent_people":[],
    "favourite_people":[],
}

def settings_path():
    p=Path.home()/".reunion-companion"
    p.mkdir(parents=True,exist_ok=True)
    return p/"ffd-presentation.json"

def load_settings():
    p=settings_path()
    data={}
    if p.exists():
        try:
            data=json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            data={}
    result=dict(DEFAULT_SETTINGS)
    result.update({k:v for k,v in data.items() if k in DEFAULT_SETTINGS})
    if not isinstance(result.get("recent_people"),list):result["recent_people"]=[]
    if not isinstance(result.get("favourite_people"),list):result["favourite_people"]=[]
    return result

def save_settings(settings):
    p=settings_path()
    clean=dict(DEFAULT_SETTINGS)
    clean.update({k:v for k,v in settings.items() if k in DEFAULT_SETTINGS})
    p.write_text(json.dumps(clean,indent=2,ensure_ascii=False),encoding="utf-8")
    return clean

def update_setting(name,value):
    s=load_settings()
    if name not in DEFAULT_SETTINGS:
        raise KeyError(name)
    s[name]=value
    return save_settings(s)

def toggle_presentation():
    s=load_settings()
    s["presentation_mode"]=not bool(s.get("presentation_mode"))
    save_settings(s)
    return s["presentation_mode"]

def remember_person(pid,display_name):
    s=load_settings()
    entry={"id":int(pid),"display_name":str(display_name)}
    recent=[x for x in s["recent_people"] if int(x.get("id",-1))!=int(pid)]
    recent.insert(0,entry)
    s["recent_people"]=recent[:8]
    save_settings(s)
    return s["recent_people"]

def recent_people(db):
    s=load_settings()
    out=[]
    for item in s["recent_people"]:
        row=db.execute("SELECT id,display_name,gedcom_xref FROM people WHERE id=?",(item.get("id"),)).fetchone()
        if row:out.append(dict(row))
    return out

def favourite_people(db):
    s=load_settings()
    out=[]
    for item in s["favourite_people"]:
        row=db.execute("SELECT id,display_name,gedcom_xref FROM people WHERE id=?",(item.get("id"),)).fetchone()
        if row:out.append(dict(row))
    return out

def featured_people(db,limit=6):
    # Prefer the family-relevant people we have been using during development.
    preferred=[
        "Mervyn Neil Knuckey",
        "Elaine Fay Cox",
        "Victor Alexander Knuckey",
        "Charles Henry James Knuckey",
        "James Knuckey",
        "Lionel George Waight",
    ]
    out=[]
    seen=set()
    for name in preferred:
        row=db.execute(
            "SELECT id,display_name,gedcom_xref FROM people WHERE lower(display_name)=lower(?) LIMIT 1",
            (name,)
        ).fetchone()
        if row:
            d=dict(row);out.append(d);seen.add(d["id"])
    if len(out)<limit:
        for row in db.execute("SELECT id,display_name,gedcom_xref FROM people ORDER BY id LIMIT ?",(limit*3,)).fetchall():
            if row["id"] not in seen:
                out.append(dict(row));seen.add(row["id"])
                if len(out)>=limit:break
    return out[:limit]

def family_branding(db):
    s=load_settings()
    credit=s["research_credit"]
    # If the configured credit person does not exist, stay generic rather
    # than presenting an invented genealogy attribution.
    row=db.execute("SELECT id FROM people WHERE lower(display_name)=lower(?) LIMIT 1",(credit,)).fetchone()
    return {
        "family_title":s["family_title"] or "Family History",
        "research_credit":credit if row else None,
        "presentation_mode":bool(s["presentation_mode"]),
    }

def dashboard_counts(db):
    counts={}
    for table,label in (
        ("people","People"),("families","Families"),("sources","Sources"),("media","Media")
    ):
        try:counts[label]=db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except Exception:counts[label]=0
    try:
        counts["Places"]=db.execute(
            "SELECT COUNT(DISTINCT trim(place_text)) FROM events WHERE coalesce(trim(place_text),'')<>''"
        ).fetchone()[0]
    except Exception:
        counts["Places"]=0
    return counts

def people_index(db,limit=500):
    return [dict(x) for x in db.execute(
        "SELECT id,display_name,gedcom_xref,sex FROM people ORDER BY surname,given_names,display_name LIMIT ?",
        (limit,)
    ).fetchall()]

def families_index(db,limit=500):
    rows=db.execute("""SELECT f.id,
      h.display_name husband,w.display_name wife,
      f.marriage_date,f.marriage_place
      FROM families f
      LEFT JOIN family_members hm ON hm.family_id=f.id AND hm.role='Husband'
      LEFT JOIN people h ON h.id=hm.person_id
      LEFT JOIN family_members wm ON wm.family_id=f.id AND wm.role='Wife'
      LEFT JOIN people w ON w.id=wm.person_id
      ORDER BY coalesce(h.display_name,w.display_name,''),f.id LIMIT ?""",(limit,)).fetchall()
    return [dict(x) for x in rows]

def report_directory():
    return Path.home()/"Documents"/"Reunion Companion Reports"

def _publication_kind(path):
    n=path.name.lower()
    if "professional_family_chapter" in n:return "Family Chapter"
    if "professional_family_history" in n:return "Family-history Book"
    if "descendant_chart" in n:return "Descendant Chart"
    if "biography" in n:return "Biography"
    if "profile" in n:return "Profile"
    if "person" in n:return "Person Report"
    return "Publication"

def publication_library(limit=100):
    root=report_directory()
    if not root.exists():
        return []
    items=[]
    for p in root.iterdir():
        if not p.is_file() or p.suffix.lower() not in {".html",".pdf"}:
            continue
        try:
            stat=p.stat()
        except OSError:
            continue
        items.append({
            "name":p.stem.replace("_"," "),
            "filename":p.name,
            "path":str(p),
            "format":p.suffix[1:].upper(),
            "kind":_publication_kind(p),
            "modified":datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="minutes"),
            "mtime":stat.st_mtime,
        })
    items.sort(key=lambda x:x["mtime"],reverse=True)
    return items[:limit]

def latest_publication():
    items=publication_library(1)
    return items[0] if items else None

def safe_report_path(raw):
    root=report_directory().resolve()
    p=Path(raw).expanduser().resolve()
    try:
        p.relative_to(root)
    except ValueError:
        raise ValueError("Only files in Reunion Companion Reports can be opened from the Books library.")
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(str(p))
    return p

def about_model(db):
    branding=family_branding(db)
    return {
        **branding,
        "product":"Reunion Companion",
        "mission":"A companion to Reunion for exploring, publishing and preserving family history.",
        "principle":"Reunion remains the authoritative genealogy editor.",
    }
