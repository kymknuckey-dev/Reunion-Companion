from __future__ import annotations
import re
import html
from urllib.parse import quote
from .branding import home_brand_html

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
  {home_brand_html()}
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

def _discovery_group_rank(person):
    kind=(person or {}).get("_identity_match_kind","")
    return {"recorded-name":0,"recorded-given":0,"given-variant":1,"spouse-surname":2,"given-variant-spouse-surname":2}.get(kind,1)

def _discovery_display_quality(p):
    name=(p or {}).get("display_name","") or ""
    score=0
    if any(ch.isdigit() for ch in name):score-=4
    if "," in name:score-=2
    words=re.findall(r"[A-Za-zÀ-ÿ'’-]+",name)
    if len(words)>=3:score+=2
    elif len(words)==2:score+=1
    else:score-=2
    return score

def _discovery_choice_sort(choice):
    p=choice.get("person",{})
    group=choice.get("identity_group_rank",_discovery_group_rank(p))
    kind=choice.get("identity_match_kind") or p.get("_identity_match_kind","")
    assoc_rank={"given-variant-spouse-surname":0,"spouse-surname":1}.get(kind,2) if group>=2 else 0
    return (group,
            0 if choice.get("question_relevant") else 1,
            assoc_rank,
            -_discovery_display_quality(p),
            -p.get("_identity_score",0),
            (choice.get("label") or p.get("display_name","")).casefold(),
            p.get("id",0))

def _discovery_cards(choices,q):
    cards=[]
    for c in choices:
        p=c.get("person",{});label=c.get("label") or p.get("display_name","")
        reason=c.get("identity_reason") or p.get("_identity_match_reason","")
        recognition=c.get("recognition","")
        rel=f"<div class='search-discovery-reason'>{esc(reason)}</div>" if reason and reason not in ("Exact recorded name","Recorded name") else ""
        recog=f"<div class='meta'>{esc(recognition)}</div>" if recognition else ""
        fact=f"<div class='rq-relevance'>{esc(c.get('relevance_label'))}</div>" if c.get("question_relevant") and c.get("relevance_label") else ""
        cards.append(f"<a class='search-discovery-card' href='/search?q={quote(q)}&selected={p.get('id','')}'><strong>{esc(p.get('display_name'))}</strong><div class='meta'>{esc(label[len(p.get('display_name','')):].strip())}</div>{recog}{rel}{fact}<div class='search-discovery-action'>Answer using this person →</div></a>")
    return "".join(cards)

def _discovery_question_result(r,q,presentation=False):
    if not r:
        return ""
    if r.get("kind")=="identity-choice":
        choices=sorted(r.get("choices",[]),key=_discovery_choice_sort)
        direct=[c for c in choices if c.get("identity_group_rank",_discovery_group_rank(c.get("person",{})))<2]
        associated=[c for c in choices if c not in direct]
        # QA Pass 3: do not force every identity interpretation through one score.
        # Strong explained spouse-surname interpretations get their own first-screen
        # lane.  This makes a person known by a partner's surname prominent without
        # changing the authoritative Reunion name or suppressing literal records.
        best_likely=[c for c in associated
                     if (c.get("identity_match_kind") or c.get("person",{}).get("_identity_match_kind",""))
                        in ("spouse-surname","given-variant-spouse-surname")
                     and _discovery_display_quality(c.get("person",{}))>=1]
        other_associated=[c for c in associated if c not in best_likely]
        chunks=[]
        relevant=[c for c in choices if c.get("question_relevant")]
        if relevant:
            domain=(r.get("question_domain") or "requested information").replace("_"," ")
            chunks.append(f"<div class='rq-choice-section-title'>Matches with {esc(domain)} information</div>")
        if best_likely:
            chunks.append("<div class='rq-choice-section'><div class='rq-choice-section-title'>Best likely matches</div><div class='search-discovery-grid'>"+_discovery_cards(best_likely[:6],q)+"</div></div>")
        if direct:
            visible=direct[:6];extra=direct[6:]
            chunks.append("<div class='rq-choice-section'><div class='rq-choice-section-title'>People recorded with this name</div><div class='search-discovery-grid'>"+_discovery_cards(visible,q)+"</div></div>")
            if extra:
                chunks.append(f"<details class='rq-other-matches'><summary>More people recorded with this name ({len(extra)})</summary><div class='search-discovery-grid'>{_discovery_cards(extra,q)}</div></details>")
        if other_associated:
            chunks.append("<div class='rq-choice-section'><div class='rq-choice-section-title'>Other family/name associations</div><div class='search-discovery-grid'>"+_discovery_cards(other_associated[:8],q)+"</div></div>")
            if len(other_associated)>8:
                chunks.append(f"<details class='rq-other-matches'><summary>More family/name association matches ({len(other_associated)-8})</summary><div class='search-discovery-grid'>{_discovery_cards(other_associated[8:],q)}</div></details>")
        nonrelevant=[c for c in choices if not c.get("question_relevant")]
        if relevant and nonrelevant:
            chunks.append(f"<details class='rq-other-matches'><summary>Other matches — requested information not currently recorded ({len(nonrelevant)})</summary></details>")
        return ("<div class='search-discovery'><h2>Possible people</h2>"
                "<p class='meta'>Companion found more than one person who could match the name in your question. The recorded Reunion name remains authoritative.</p>"
                +"".join(chunks)+"</div>")
    answer=esc(r.get("answer","")).replace("\n\n","</p><p>")
    reason=r.get("identity_match_reason","")
    why=f"<div class='search-discovery-reason'>{esc(reason)}. Reunion's recorded name has not been changed.</div>" if reason else ""
    p=r.get("context_person") or r.get("question_subject")
    link=f"<p><a class='button secondary' href='/person/{p['id']}'>View {esc(p['display_name'])} →</a></p>" if p else ""
    return f"<div class='search-discovery'><h2>Answer</h2>{why}<p>{answer}</p>{link}</div>"

def search_body(db,q,search_people,presentation=False,question_result=None):
    q=(q or "").strip()
    rows=search_people(db,q) if q and question_result is None else []

    if question_result is not None:
        result_html=_discovery_question_result(question_result,q,presentation)
    elif q:
        def person_row(p):
            reason=p.get('_identity_match_reason')
            why=(f"<div class='search-discovery-reason'>{esc(reason)}</div>" if reason and reason not in ('Exact recorded name','Recorded name','Recorded given name') else "")
            return (f"<a class='result' href='/person/{p['id']}'><strong>{esc(p['display_name'])}</strong>"
                    + ("" if presentation else f" <span class='meta'>{esc(p.get('gedcom_xref'))}</span>") + why + "</a>")
        direct=[p for p in rows if _discovery_group_rank(p)<2]
        associated=[p for p in rows if p not in direct]
        def association_key(p):
            kind=p.get("_identity_match_kind","")
            assoc_rank={"given-variant-spouse-surname":0,"spouse-surname":1}.get(kind,2)
            return (assoc_rank,-_discovery_display_quality(p),-p.get("_identity_score",0),p.get("display_name","").casefold(),p.get("id",0))
        associated=sorted(associated,key=association_key)
        best_likely=[p for p in associated
                     if p.get("_identity_match_kind") in ("spouse-surname","given-variant-spouse-surname")
                     and _discovery_display_quality(p)>=1]
        other_associated=[p for p in associated if p not in best_likely]
        chunks=[]
        if best_likely:
            chunks.append("<div class='rq-choice-section-title'>Best likely matches</div>"+"".join(person_row(p) for p in best_likely[:6]))
        if direct:
            chunks.append("<div class='rq-choice-section-title' style='margin-top:18px'>People recorded with this name</div>"+"".join(person_row(p) for p in direct))
        if other_associated:
            chunks.append("<div class='rq-choice-section-title' style='margin-top:18px'>Other family/name associations</div>"+"".join(person_row(p) for p in other_associated))
        result_html="".join(chunks) or "<p>No matches found.</p>"
    else:
        result_html="<p class='meta'>Search for a person, or ask a question about someone in your family history.</p>"

    return f"""
<div class='ffd-page-heading'>
  <div class='ffd-eyebrow'>Explore the family</div>
  <h1>Search the Family</h1>
  <p class='meta'>Find a person, or ask a question about someone in your family history.</p>
</div>
<div class='card'>
  <form class='ffd-search' action='/search' method='get'>
    <input name='q' value='{esc(q)}' placeholder='Susan Jones or Where did Susan Knuckey live?'>
    <button>Search</button>
  </form>
</div>
<div class='card'>
  <h2>{'Results' if q else 'Search'}</h2>
  {result_html}
</div>
"""

