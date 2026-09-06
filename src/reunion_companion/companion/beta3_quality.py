from __future__ import annotations

import re
from collections import Counter
from datetime import date

from .beta2_research import place_variants

_YEAR_RE = re.compile(r"\b(1[5-9]\d{2}|20\d{2})\b")
_CORE_EVENT_TYPES = ("Birth", "Marriage", "Death", "Burial", "Cremation")


def _table_exists(db, name):
    return db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone() is not None

def _columns(db, table):
    return {r[1] for r in db.execute(f"PRAGMA table_info({table})").fetchall()}

def _event_expr(db, col):
    return col if col in _columns(db,"events") else f"NULL AS {col}"

def _year(text):
    if not text:
        return None
    m = _YEAR_RE.search(str(text))
    return int(m.group(1)) if m else None


def _person_era(db, person_id, preferred_text=None):
    """Best available event year for simple, explainable actionability."""
    y = _year(preferred_text)
    if y:
        return y
    if "date_text" not in _columns(db,"events"):
        return None
    rows = db.execute(
        """SELECT date_text FROM events
           WHERE person_id=? AND event_type IN ('Birth','Death','Burial','Cremation')
             AND coalesce(trim(date_text),'')<>''
           ORDER BY CASE event_type WHEN 'Death' THEN 0 WHEN 'Burial' THEN 1 WHEN 'Cremation' THEN 2 ELSE 3 END,id""",
        (person_id,),
    ).fetchall()
    years = [y for y in (_year(r["date_text"]) for r in rows) if y]
    return max(years) if years else None



def era_bucket(year, current_year=None):
    """Rolling genealogical era used for quality drill-down."""
    current_year = current_year or date.today().year
    if year is None:
        return "unknown", "Unknown / insufficient date context"
    age = current_year - int(year)
    if age < 100:
        return "last-100", "Last 100 years"
    if age < 200:
        return "100-200", "100–200 years ago"
    return "over-200", "More than 200 years ago"


def quality_drilldown(items, current_year=None):
    """Counts by event type and rolling era without changing actionability."""
    event_counts=Counter(x.get("event_type") or "Fact" for x in items)
    era_counts=Counter(era_bucket(x.get("year"), current_year)[0] for x in items)
    return {"by_type":dict(sorted(event_counts.items())), "by_era":dict(era_counts)}


def filter_quality_items(items, event_type=None, era=None, current_year=None):
    out=items
    if event_type:
        out=[x for x in out if (x.get("event_type") or "Fact")==event_type]
    if era:
        out=[x for x in out if era_bucket(x.get("year"),current_year)[0]==era]
    return out

def _actionability(year, event_type, issue):
    """Return transparent first-pass quality classification, not a hidden score."""
    event_type = event_type or "Fact"
    core = event_type in _CORE_EVENT_TYPES
    if year is None:
        if core:
            return "review", "Review", "Core life event; era is not yet clear"
        return "low", "Low opportunity", "No dated context to suggest an immediate cleanup opportunity"
    if year >= 1900:
        reason = "20th/21st-century record; likely practical to verify"
        if issue == "missing":
            reason = "Recent core record with incomplete recorded information"
        return "actionable", "Actionable", reason
    if year >= 1800:
        return "review", "Review", "19th-century record; potentially practical to improve"
    return "low", "Low opportunity", f"Early record ({year}); retain for review but do not foreground"


def _event_supported(db, event_id):
    return bool(db.execute("SELECT 1 FROM event_sources WHERE event_id=? LIMIT 1", (event_id,)).fetchone() or
                db.execute("SELECT 1 FROM event_media WHERE event_id=? LIMIT 1", (event_id,)).fetchone())


def _family_supported(db, family_id):
    return bool(db.execute("SELECT 1 FROM family_sources WHERE family_id=? LIMIT 1", (family_id,)).fetchone() or
                db.execute("SELECT 1 FROM family_media WHERE family_id=? LIMIT 1", (family_id,)).fetchone())


def _family_display(db, family_id):
    names = [r["display_name"] for r in db.execute(
        """SELECT p.display_name FROM family_members fm JOIN people p ON p.id=fm.person_id
           WHERE fm.family_id=? AND lower(fm.role) IN ('husband','wife','spouse') ORDER BY p.id""",
        (family_id,),
    ).fetchall()]
    return " & ".join(names) if names else f"Family {family_id}"


def missing_information_items(db, limit=5000):
    """Incomplete fields on already-recorded core life events/families.

    Deliberately does not create a missing Death event: that research-completeness
    workflow belongs in Priorities. Improve deals with incomplete data already held.
    """
    out = []
    ec=_columns(db,"events")
    date_sel="e.date_text" if "date_text" in ec else "NULL AS date_text"
    place_sel="e.place_text" if "place_text" in ec else "NULL AS place_text"
    missing_tests=[]
    if "date_text" in ec: missing_tests.append("coalesce(trim(e.date_text),'')=''")
    if "place_text" in ec: missing_tests.append("coalesce(trim(e.place_text),'')=''")
    where_missing=" OR ".join(missing_tests) or "0"
    rows = db.execute(
        f"""SELECT e.id,e.person_id,e.event_type,{date_sel},{place_sel},p.display_name
           FROM events e JOIN people p ON p.id=e.person_id
           WHERE e.event_type IN ('Birth','Death','Burial','Cremation')
             AND ({where_missing})
           ORDER BY p.display_name,e.id"""
    ).fetchall()
    for r in rows:
        missing=[]
        if not (r["date_text"] or "").strip(): missing.append("date")
        if not (r["place_text"] or "").strip(): missing.append("place")
        yr=_person_era(db,r["person_id"],r["date_text"])
        key,label,reason=_actionability(yr,r["event_type"],"missing")
        out.append({
            "kind":"missing-information","scope":"person","id":r["id"],"event_id":r["id"],
            "person_id":r["person_id"],"display_name":r["display_name"],"event_type":r["event_type"],
            "date_text":r["date_text"],"place_text":r["place_text"],"missing_fields":missing,
            "current_value":"; ".join(x for x in ((r["date_text"] or "").strip(),(r["place_text"] or "").strip()) if x) or "Not recorded",
            "actionability":key,"priority_label":label,"reason":reason,"year":yr,
        })
    # Marriage is stored on families rather than person events.
    family_rows=[]
    if _table_exists(db,"families") and _table_exists(db,"family_members") and {"marriage_date","marriage_place"} <= _columns(db,"families"):
        family_rows=db.execute(
        """SELECT id,marriage_date,marriage_place FROM families
           WHERE coalesce(trim(marriage_date),'')<>'' OR coalesce(trim(marriage_place),'')<>''
           ORDER BY id"""
        ).fetchall()
    for f in family_rows:
        missing=[]
        if not (f["marriage_date"] or "").strip(): missing.append("date")
        if not (f["marriage_place"] or "").strip(): missing.append("place")
        if not missing: continue
        yr=_year(f["marriage_date"])
        key,label,reason=_actionability(yr,"Marriage","missing")
        out.append({
            "kind":"missing-information","scope":"family","id":f["id"],"family_id":f["id"],
            "person_id":None,"display_name":_family_display(db,f["id"]),"event_type":"Marriage",
            "date_text":f["marriage_date"],"place_text":f["marriage_place"],"missing_fields":missing,
            "current_value":"; ".join(x for x in ((f["marriage_date"] or "").strip(),(f["marriage_place"] or "").strip()) if x) or "Not recorded",
            "actionability":key,"priority_label":label,"reason":reason,"year":yr,
        })
    rank={"actionable":0,"review":1,"low":2}
    out.sort(key=lambda x:(rank.get(x["actionability"],9),-(x["year"] or 0),x["display_name"],x["event_type"]))
    return out[:limit]


def unsourced_information_items(db, limit=5000):
    out=[]
    ec=_columns(db,"events")
    date_sel="e.date_text" if "date_text" in ec else "NULL AS date_text"
    place_sel="e.place_text" if "place_text" in ec else "NULL AS place_text"
    value_sel="e.value_text" if "value_text" in ec else "NULL AS value_text"
    source_test="NOT EXISTS(SELECT 1 FROM event_sources es WHERE es.event_id=e.id)" if _table_exists(db,"event_sources") else "1"
    media_test="NOT EXISTS(SELECT 1 FROM event_media em WHERE em.event_id=e.id)" if _table_exists(db,"event_media") else "1"
    rows=db.execute(
        f"""SELECT e.id,e.person_id,e.event_type,{date_sel},{place_sel},{value_sel},p.display_name
           FROM events e JOIN people p ON p.id=e.person_id
           WHERE e.event_type<>'Changed' AND {source_test} AND {media_test}
           ORDER BY p.display_name,e.id"""
    ).fetchall()
    for r in rows:
        yr=_person_era(db,r["person_id"],r["date_text"])
        key,label,reason=_actionability(yr,r["event_type"],"unsourced")
        current="; ".join(x for x in ((r["date_text"] or "").strip(),(r["place_text"] or "").strip(),(r["value_text"] or "").strip()) if x) or "Recorded fact"
        out.append({
            "kind":"unsourced-information","scope":"person","id":r["id"],"event_id":r["id"],
            "person_id":r["person_id"],"display_name":r["display_name"],"event_type":r["event_type"],
            "date_text":r["date_text"],"place_text":r["place_text"],"current_value":current,
            "actionability":key,"priority_label":label,"reason":reason,"year":yr,
        })
    family_rows=[]
    if (_table_exists(db,"families") and _table_exists(db,"family_members") and _table_exists(db,"family_sources") and _table_exists(db,"family_media")
            and {"marriage_date","marriage_place"} <= _columns(db,"families")):
        family_rows=db.execute(
            """SELECT id,marriage_date,marriage_place FROM families
               WHERE (coalesce(trim(marriage_date),'')<>'' OR coalesce(trim(marriage_place),'')<>'')
                 AND NOT EXISTS(SELECT 1 FROM family_sources fs WHERE fs.family_id=families.id)
                 AND NOT EXISTS(SELECT 1 FROM family_media fm WHERE fm.family_id=families.id)
               ORDER BY id"""
        ).fetchall()
    for f in family_rows:
        yr=_year(f["marriage_date"])
        key,label,reason=_actionability(yr,"Marriage","unsourced")
        out.append({
            "kind":"unsourced-information","scope":"family","id":f["id"],"family_id":f["id"],
            "person_id":None,"display_name":_family_display(db,f["id"]),"event_type":"Marriage",
            "date_text":f["marriage_date"],"place_text":f["marriage_place"],
            "current_value":"; ".join(x for x in ((f["marriage_date"] or "").strip(),(f["marriage_place"] or "").strip()) if x) or "Recorded marriage",
            "actionability":key,"priority_label":label,"reason":reason,"year":yr,
        })
    rank={"actionable":0,"review":1,"low":2}
    out.sort(key=lambda x:(rank.get(x["actionability"],9),-(x["year"] or 0),x["display_name"],x["event_type"]))
    return out[:limit]


def _summary(items):
    by_action=Counter(x["actionability"] for x in items)
    by_type=Counter(x["event_type"] for x in items)
    return {
        "total":len(items),"actionable":by_action["actionable"],"review":by_action["review"],"low":by_action["low"],
        "by_type":dict(sorted(by_type.items())),
    }


def quick_wins(db):
    missing=missing_information_items(db,100000)
    unsourced=unsourced_information_items(db,100000)
    missing_media=db.execute("SELECT COUNT(*) FROM media WHERE exists_on_disk=0").fetchone()[0]
    pict=db.execute("""SELECT COUNT(*) FROM media WHERE lower(file_path) LIKE '%.pict'
      OR lower(file_path) LIKE '%.pct' OR lower(file_path) LIKE '%.pic'""").fetchone()[0]
    mb=db.execute("SELECT COUNT(*) FROM events WHERE event_type='Birth' AND coalesce(trim(place_text),'')='' ").fetchone()[0]
    md=db.execute("SELECT COUNT(*) FROM events WHERE event_type='Death' AND coalesce(trim(place_text),'')='' ").fetchone()[0]
    untitled=db.execute("SELECT COUNT(*) FROM sources WHERE coalesce(trim(display_text),'')='' OR display_text=gedcom_xref").fetchone()[0]
    dup=sum(r["n"]-1 for r in db.execute("""SELECT lower(trim(display_text)) k,COUNT(*) n FROM sources
      WHERE coalesce(trim(display_text),'')<>'' GROUP BY k HAVING n>1""").fetchall())
    pv=place_variants(db,1000)
    ms=_summary(missing); us=_summary(unsourced)
    return {
        "place_variant_groups":len(pv),
        "missing_information":ms["total"],"missing_information_actionable":ms["actionable"],"missing_information_summary":ms,
        "unsourced_information":us["total"],"unsourced_information_actionable":us["actionable"],"unsourced_information_summary":us,
        # Compatibility key for person views/tests while the UI migrates.
        "unsourced_events":len([x for x in unsourced if x["scope"]=="person"]),
        "missing_media":missing_media,"legacy_pict":pict,"missing_birth_place":mb,"missing_death_place":md,
        "untitled_sources":untitled,"duplicate_source_titles":dup,
    }


def quality_items(db,kind,limit=2000):
    if kind=="missing-information":
        return missing_information_items(db,limit)
    if kind in ("unsourced-information","unsourced-events"):
        items=unsourced_information_items(db,limit if kind=="unsourced-information" else limit*2)
        if kind=="unsourced-events":
            items=[x for x in items if x["scope"]=="person"][:limit]
        return items
    if kind=="missing-birth-place":
        q="""SELECT e.id,e.date_text,p.id person_id,p.display_name FROM events e JOIN people p ON p.id=e.person_id
          WHERE e.event_type='Birth' AND coalesce(trim(e.place_text),'')='' ORDER BY p.display_name LIMIT ?"""
    elif kind=="missing-death-place":
        q="""SELECT e.id,e.date_text,p.id person_id,p.display_name FROM events e JOIN people p ON p.id=e.person_id
          WHERE e.event_type='Death' AND coalesce(trim(e.place_text),'')='' ORDER BY p.display_name LIMIT ?"""
    elif kind=="missing-media":
        return [dict(x) for x in db.execute("SELECT * FROM media WHERE exists_on_disk=0 ORDER BY title LIMIT ?",(limit,)).fetchall()]
    elif kind=="legacy-pict":
        return [dict(x) for x in db.execute("""SELECT * FROM media WHERE lower(file_path) LIKE '%.pict'
          OR lower(file_path) LIKE '%.pct' OR lower(file_path) LIKE '%.pic' ORDER BY title LIMIT ?""",(limit,)).fetchall()]
    elif kind=="untitled-sources":
        return [dict(x) for x in db.execute("SELECT * FROM sources WHERE coalesce(trim(display_text),'')='' OR display_text=gedcom_xref ORDER BY id LIMIT ?",(limit,)).fetchall()]
    elif kind=="duplicate-sources":
        return [dict(x) for x in db.execute("""SELECT display_text,group_concat(id) ids,COUNT(*) n FROM sources
          WHERE coalesce(trim(display_text),'')<>'' GROUP BY lower(trim(display_text)) HAVING n>1 ORDER BY n DESC LIMIT ?""",(limit,)).fetchall()]
    else:
        return []
    return [dict(x) for x in db.execute(q,(limit,)).fetchall()]


def person_quality(db,pid):
    flags=[]
    for x in missing_information_items(db,100000):
        if x.get("person_id")==pid:
            flags.append({"kind":"Missing information","detail":f"{x['event_type']}: missing {' and '.join(x['missing_fields'])}","event_id":x.get("event_id")})
    for x in unsourced_information_items(db,100000):
        if x.get("person_id")==pid:
            flags.append({"kind":"Unsourced information","detail":x.get("event_type") or x.get("date_text"),"event_id":x.get("event_id")})
    return flags
