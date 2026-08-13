from __future__ import annotations
import html

def esc(v):
    return html.escape("" if v is None else str(v))

def _count(db,table):
    try:
        return db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except Exception:
        return 0

def _place_count(db):
    try:
        return db.execute(
            "SELECT COUNT(DISTINCT trim(place_text)) FROM events "
            "WHERE coalesce(trim(place_text),'')<>''"
        ).fetchone()[0]
    except Exception:
        return 0

def _research_credit(db):
    row=db.execute(
        "SELECT id,display_name FROM people "
        "WHERE lower(display_name)=lower(?) LIMIT 1",
        ("Mervyn Neil Knuckey",)
    ).fetchone()
    return dict(row) if row else None

def featured_people(db,limit=6):
    # Prefer recently explored people, then fill with stable family-history suggestions.
    result=[];seen=set()
    try:
        db.execute("CREATE TABLE IF NOT EXISTS companion_recent_people(person_id INTEGER PRIMARY KEY, viewed_at TEXT NOT NULL)")
        rows=db.execute("SELECT p.id,p.display_name,p.gedcom_xref FROM companion_recent_people r JOIN people p ON p.id=r.person_id ORDER BY r.viewed_at DESC LIMIT ?",(limit,)).fetchall()
        for row in rows: result.append(dict(row));seen.add(row["id"])
    except Exception: pass
    preferred=["Mervyn Neil Knuckey","Elaine Fay Cox","Victor Alexander Knuckey","Charles Henry James Knuckey","James Knuckey","Lionel George Waight"]
    for name in preferred:
        if len(result)>=limit:break
        row=db.execute("SELECT id,display_name,gedcom_xref FROM people WHERE lower(display_name)=lower(?) LIMIT 1",(name,)).fetchone()
        if row and row["id"] not in seen: result.append(dict(row));seen.add(row["id"])
    if len(result)<limit:
        for row in db.execute("SELECT id,display_name,gedcom_xref FROM people ORDER BY id LIMIT ?",(limit*3,)).fetchall():
            if row["id"] not in seen:result.append(dict(row));seen.add(row["id"])
            if len(result)>=limit:break
    return result[:limit]

def home_body(db,quality_counts,presentation=False):
    from .family_files import active_family_file
    ff=active_family_file(db)
    family_title=ff['display_name'] if ff else 'Family History'
    credit=_research_credit(db)
    people=featured_people(db)

    stats={
        "People":_count(db,"people"),
        "Families":_count(db,"families"),
        "Sources":_count(db,"sources"),
        "Media":_count(db,"media"),
        "Places":_place_count(db),
    }

    credit_html=(
        f"<p class='ffd-credit'>Research begun by "
        f"<strong>{esc(credit['display_name'])}</strong></p>"
        if credit else
        "<p class='ffd-credit'>Family history research preserved in Reunion</p>"
    )

    people_rows=[]
    for p in people:
        code_html="" if presentation else f"<span class='meta'> {esc(p.get('gedcom_xref'))}</span>"
        people_rows.append(
            f"<a class='result' href='/person/{p['id']}'>"
            f"<strong>{esc(p['display_name'])}</strong>{code_html}</a>"
        )
    people_html="".join(people_rows) or "<p class='meta'>No people are currently available.</p>"

    stats_html="".join(
        f"<div class='card ffd-stat'><div class='meta'>{esc(label)}</div>"
        f"<div class='kpi'>{value:,}</div></div>"
        for label,value in stats.items()
    )

    quality_total=sum(quality_counts.values())
    presentation_explore=f"""<h2 class='ffd-section'>Explore</h2>
<div class='grid'>
  <a class='card quick ffd-explore' href='/search'><h2>Find a Person</h2><p>Search the family and open a person’s history.</p></a>
  <a class='card quick ffd-explore' href='/reports'><h2>Reports</h2><p>Open and manage generated family-history reports.</p></a>
</div>"""
    research_explore=f"""<h2 class='ffd-section'>Explore</h2>
<div class='grid'>
  <a class='card quick ffd-explore' href='/search'><h2>Find a Person</h2><p>Search the family and open a person’s history.</p></a>
  <a class='card quick ffd-explore' href='/research'><h2>Explore Research</h2><p>Review research observations across the family history.</p></a>
  <a class='card quick ffd-explore' href='/quality'><h2>Improve the Data</h2><p>{quality_total:,} current review opportunities.</p></a>
  <a class='card quick ffd-explore' href='/places'><h2>Places</h2><p>Explore recorded places and possible variants.</p></a>
  <a class='card quick ffd-explore' href='/sources'><h2>Sources</h2><p>Explore sources and their use across the dataset.</p></a>
  <a class='card quick ffd-explore' href='/media'><h2>Media</h2><p>Explore photos, documents and other media.</p></a>
  <a class='card quick ffd-explore' href='/data'><h2>Data Import</h2><p>Review and safely refresh the Reunion GEDCOM data.</p></a>
  <a class='card quick ffd-explore' href='/reports'><h2>Reports</h2><p>Open and manage generated family-history reports.</p></a>
</div>"""

    return f"""
<section class='ffd-hero'>
  <div class='ffd-eyebrow'>Welcome to your family history</div>
  <h1>{esc(family_title)}</h1>
  {credit_html}
  <p class='ffd-intro'>
    Explore the people, families, evidence and publications preserved in Reunion,
    and continue building on that research.
  </p>
  <form class='ffd-search' action='/search' method='get'>
    <input id='family-search' name='q'
      placeholder='Search the family history — e.g. Mervyn, Waight, Hunter'>
    <button>Search</button>
  </form>
</section>

{presentation_explore if presentation else research_explore}
<div class='ffd-two'>
  <div>
    <h2 class='ffd-section'>Family to Explore</h2>
    <div class='card'>{people_html}</div>
  </div>
  <div>
    <h2 class='ffd-section'>A Living Family History</h2>
    <div class='card'>
      <p>
        Reunion remains the authoritative family-history record.
        Companion helps make that work easier to explore, review and share.
      </p>
      <p class='meta'>Research preserved for future generations.</p>
    </div>
  </div>
</div>

<h2 class='ffd-section'>Family History at a Glance</h2>
<div class='grid'>{stats_html}</div>
"""

def search_body(db,q,search_people,presentation=False):
    q=(q or "").strip()
    rows=search_people(db,q) if q else []

    result_html=""
    if q:
        result_html="".join(
            f"<a class='result' href='/person/{p['id']}'>"
            f"<strong>{esc(p['display_name'])}</strong>" + ("" if presentation else f" <span class='meta'>{esc(p.get('gedcom_xref'))}</span>") + "</a>"
            for p in rows
        ) or "<p>No matches found.</p>"
    else:
        result_html="<p class='meta'>Enter a name above to search the family history.</p>"

    return f"""
<div class='ffd-page-heading'>
  <div class='ffd-eyebrow'>Explore the family</div>
  <h1>Search Family History</h1>
</div>
<div class='card'>
  <form class='ffd-search' action='/search' method='get'>
    <input name='q' value='{esc(q)}' placeholder='Search for a person'>
    <button>Search</button>
  </form>
</div>
<div class='card'>
  <h2>{'Results' if q else 'Search'}</h2>
  {result_html}
</div>
"""
