from __future__ import annotations

from html import escape
from urllib.parse import quote

STATE_LABELS = {
    "new": "New",
    "deferred": "Decide Later",
    "waiting_for_reunion": "Waiting for Reunion",
    "already_known": "Already Known",
    "rejected": "Not This Person",
    "confirmed_complete": "Confirmed Complete",
}

STATE_ORDER = (
    "new",
    "waiting_for_reunion",
    "deferred",
    "already_known",
    "rejected",
    "confirmed_complete",
)


def _person_name(row):
    for key in ("display_name", "name", "raw_name"):
        try:
            value=row[key]
        except Exception:
            continue
        if value:
            return str(value)
    return f"Person {row['person_id']}"


def discovery_review_rows(db, *, state=None):
    from .ryerson_discovery_review import ensure_discovery_review_schema
    ensure_discovery_review_schema(db)

    where=""
    args=()
    if state:
        where="WHERE d.state=?"
        args=(state,)

    return db.execute(
        f"""
        SELECT d.*, p.display_name, p.raw_name
        FROM companion_external_discovery_review d
        LEFT JOIN people p ON p.id=d.person_id
        {where}
        ORDER BY
          CASE d.state
            WHEN 'new' THEN 0
            WHEN 'waiting_for_reunion' THEN 1
            WHEN 'deferred' THEN 2
            WHEN 'already_known' THEN 3
            WHEN 'rejected' THEN 4
            WHEN 'confirmed_complete' THEN 5
            ELSE 9
          END,
          lower(COALESCE(p.display_name,p.raw_name,'')),
          d.first_seen_at DESC,
          d.id DESC
        """,
        args,
    ).fetchall()


def discovery_review_groups(db):
    groups={}
    for row in discovery_review_rows(db):
        groups.setdefault(row["state"],[]).append(row)
    return groups


def _group_people(rows):
    grouped={}
    for row in rows:
        grouped.setdefault(row["person_id"],[]).append(row)
    return list(grouped.items())


def _first_event(db, person_id, event_type):
    return db.execute(
        "SELECT * FROM events WHERE person_id=? AND lower(event_type)=lower(?) ORDER BY id LIMIT 1",
        (person_id,event_type),
    ).fetchone()


def _row_value(row, *names):
    if row is None:
        return ""
    keys=set(row.keys())
    for name in names:
        if name in keys:
            value=row[name]
            if value not in (None,""):
                return str(value)
    return ""


def _event_text(row):
    if row is None:
        return "Not recorded"
    date=_row_value(row,"date_text","event_date","date","date_value")
    place=_row_value(row,"place","place_name","location")
    parts=[x for x in (date,place) if x]
    return " · ".join(parts) if parts else "Recorded"


def person_reunion_context(db, person_id):
    person=db.execute(
        "SELECT id,display_name,raw_name FROM people WHERE id=?",
        (person_id,),
    ).fetchone()
    birth=_first_event(db,person_id,"Birth")
    death=_first_event(db,person_id,"Death")
    return {
        "name": _person_name(person) if person else f"Person {person_id}",
        "birth": _event_text(birth),
        "death": _event_text(death),
    }


def _decision_forms(row, return_path):
    if row["state"] not in ("new","deferred"):
        if row["state"]=="waiting_for_reunion":
            return "<div class='small'>Accepted. Waiting for a future GEDCOM refresh to confirm the change in Reunion.</div>"
        note=row["decision_note"] or ""
        label=STATE_LABELS.get(row["state"],row["state"])
        return f"<div class='small'>{escape(label)}{': '+escape(note) if note else ''}</div>"

    rid=row["id"]
    hidden=f"<input type='hidden' name='return' value='{escape(return_path)}'>"
    parts=[
        f"<form method='post' action='/research/discovery/{rid}/waiting' style='display:inline-block;margin-right:.4rem'>{hidden}<button type='submit'>Accept for Reunion</button></form>",
        f"<form method='post' action='/research/discovery/{rid}/known' style='display:inline-block;margin-right:.4rem'>{hidden}<button type='submit'>Already Known</button></form>",
        f"<form method='post' action='/research/discovery/{rid}/reject' style='display:inline-block;margin-right:.4rem'>{hidden}<button type='submit'>Not This Person</button></form>",
    ]
    if row["state"]=="new":
        parts.append(
            f"<form method='post' action='/research/discovery/{rid}/defer' style='display:inline-block'>{hidden}<button type='submit'>Decide Later</button></form>"
        )
    return "".join(parts)


def render_discovery_review_section(db, *, preview_people=5):
    from .ryerson_discovery_review import discovery_counts
    counts=discovery_counts(db)

    out=[
        "<div class='card'>",
        "<h2>External Evidence Review</h2>",
        "<p class='meta'>Review discoveries by person. Companion remembers each decision so the same evidence is not repeatedly presented after future GEDCOM imports.</p>",
    ]

    summary=(
        f"New: {counts['new']} · "
        f"Waiting for Reunion: {counts['waiting_for_reunion']} · "
        f"Deferred: {counts['deferred']} · "
        f"Already Known: {counts['already_known']} · "
        f"Rejected: {counts['rejected']} · "
        f"Confirmed: {counts['confirmed_complete']}"
    )
    out.append(f"<div class='topic'><strong>Research review</strong><div class='small'>{escape(summary)}</div></div>")

    if counts["new"]==0:
        out.append("<p>No new person-level discoveries currently need review.</p>")
    else:
        rows=discovery_review_rows(db,state="new")
        people=_group_people(rows)
        out.append(
            f"<p><a class='button' href='/research/discoveries?state=new&page=1'>Review New Discoveries</a> "
            f"<span class='small'>{counts['new']} discoveries across {len(people)} people</span></p>"
        )
        out.append("<h3>Next people to review</h3>")
        for person_id,candidates in people[:preview_people]:
            name=_person_name(candidates[0])
            out.append(
                f"<a class='result' href='/research/discoveries?state=new&person={person_id}'>"
                f"<strong>{escape(name)}</strong>"
                f"<span class='badge warn' style='float:right'>{len(candidates)} candidate{'s' if len(candidates)!=1 else ''}</span>"
                "</a>"
            )
        if len(people)>preview_people:
            out.append(f"<div class='small'>Showing {preview_people} of {len(people)} people with new discoveries.</div>")

    out.append("</div>")
    return "".join(out)


def render_discovery_workspace(db, *, state="new", page=1, page_size=20, person_id=None):
    from .ryerson_discovery_review import discovery_counts

    if state not in STATE_ORDER:
        state="new"
    page=max(1,int(page or 1))
    page_size=max(1,min(100,int(page_size or 20)))

    rows=discovery_review_rows(db,state=state)
    people=_group_people(rows)

    if person_id is not None:
        people=[item for item in people if int(item[0])==int(person_id)]
        page=1

    total_people=len(people)
    total_pages=max(1,(total_people+page_size-1)//page_size)
    if page>total_pages:
        page=total_pages
    start=(page-1)*page_size
    shown=people[start:start+page_size]

    out=[
        "<h1>External Evidence Review</h1>",
        "<p class='meta'>Review Ryerson discoveries against the Reunion person. Decisions are saved immediately and can be resumed later.</p>",
        "<div class='card'>",
        "<div class='topic'><strong>Review state</strong><div class='small'>",
    ]
    counts=discovery_counts(db)
    links=[]
    for key in STATE_ORDER:
        links.append(
            f"<a href='/research/discoveries?state={quote(key)}&page=1'>{escape(STATE_LABELS[key])} ({counts[key]})</a>"
        )
    out.append(" · ".join(links))
    out.append("</div></div>")
    out.append(
        f"<p><a href='/research'>← Research Priorities</a> · "
        f"Showing {len(shown)} of {total_people} people · Page {page} of {total_pages}</p>"
    )
    out.append("</div>")

    if not shown:
        out.append("<div class='card'><p>No discoveries in this review state.</p></div>")
        return "".join(out)

    return_path=f"/research/discoveries?state={quote(state)}&page={page}"

    for pid,candidates in shown:
        context=person_reunion_context(db,pid)
        out.append("<div class='card'>")
        out.append(
            f"<h2><a href='/person/{pid}?tab=research'>{escape(context['name'])}</a> "
            f"<span class='small'>({len(candidates)} Ryerson candidate{'s' if len(candidates)!=1 else ''})</span></h2>"
        )
        out.append(
            "<div class='grid'>"
            "<div class='topic'><strong>Reunion record</strong>"
            f"<div class='small'>Birth: {escape(context['birth'])}</div>"
            f"<div class='small'>Death: {escape(context['death'])}</div>"
            "</div>"
            "<div class='topic'><strong>Ryerson candidates</strong>"
        )

        for row in candidates:
            fact=row["proposed_fact_key"] or "Evidence candidate"
            note=row["decision_note"] or ""
            out.append("<div class='result'>")
            out.append(f"<strong>{escape(fact)}</strong>")
            out.append(f"<div class='small'>{escape(row['source_name'])}</div>")
            if note:
                out.append(f"<div class='small'>{escape(note)}</div>")
            out.append(_decision_forms(row,return_path))
            out.append("</div>")

        out.append("</div></div></div>")

    nav=[]
    if page>1:
        nav.append(f"<a class='button' href='/research/discoveries?state={quote(state)}&page={page-1}'>Previous</a>")
    if page<total_pages:
        nav.append(f"<a class='button' href='/research/discoveries?state={quote(state)}&page={page+1}'>Next</a>")
    if nav:
        out.append("<div class='card'>"+" ".join(nav)+"</div>")

    return "".join(out)
