from .beta2_research import place_variants

def quick_wins(db):
    unsourced=db.execute("""SELECT COUNT(*) FROM events e WHERE e.event_type<>'Changed'
      AND NOT EXISTS(SELECT 1 FROM event_sources es WHERE es.event_id=e.id)
      AND NOT EXISTS(SELECT 1 FROM event_media em WHERE em.event_id=e.id)""").fetchone()[0]
    missing_media=db.execute("SELECT COUNT(*) FROM media WHERE exists_on_disk=0").fetchone()[0]
    pict=db.execute("""SELECT COUNT(*) FROM media WHERE lower(file_path) LIKE '%.pict'
      OR lower(file_path) LIKE '%.pct' OR lower(file_path) LIKE '%.pic'""").fetchone()[0]
    mb=db.execute("SELECT COUNT(*) FROM events WHERE event_type='Birth' AND coalesce(trim(place_text),'')=''").fetchone()[0]
    md=db.execute("SELECT COUNT(*) FROM events WHERE event_type='Death' AND coalesce(trim(place_text),'')=''").fetchone()[0]
    untitled=db.execute("SELECT COUNT(*) FROM sources WHERE coalesce(trim(display_text),'')='' OR display_text=gedcom_xref").fetchone()[0]
    dup=sum(r["n"]-1 for r in db.execute("""SELECT lower(trim(display_text)) k,COUNT(*) n FROM sources
      WHERE coalesce(trim(display_text),'')<>'' GROUP BY k HAVING n>1""").fetchall())
    pv=place_variants(db,1000)
    return {"place_variant_groups":len(pv),"unsourced_events":unsourced,"missing_media":missing_media,
            "legacy_pict":pict,"missing_birth_place":mb,"missing_death_place":md,
            "untitled_sources":untitled,"duplicate_source_titles":dup}

def quality_items(db,kind,limit=2000):
    if kind=="unsourced-events":
        q="""SELECT e.id,e.event_type,e.date_text,p.id person_id,p.display_name FROM events e JOIN people p ON p.id=e.person_id
          WHERE e.event_type<>'Changed' AND NOT EXISTS(SELECT 1 FROM event_sources es WHERE es.event_id=e.id)
          AND NOT EXISTS(SELECT 1 FROM event_media em WHERE em.event_id=e.id) ORDER BY p.display_name,e.id LIMIT ?"""
    elif kind=="missing-birth-place":
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
    else:return []
    return [dict(x) for x in db.execute(q,(limit,)).fetchall()]

def person_quality(db,pid):
    flags=[]
    for kind,label in (("unsourced-events","Unsourced event"),("missing-birth-place","Missing birth place"),("missing-death-place","Missing death place")):
        for x in quality_items(db,kind):
            if x.get("person_id")==pid:flags.append({"kind":label,"detail":x.get("event_type") or x.get("date_text"),"event_id":x["id"]})
    return flags
