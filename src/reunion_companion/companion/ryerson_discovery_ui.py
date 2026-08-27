from __future__ import annotations

from html import escape
from urllib.parse import quote

from .research_priority import resolve_focus_person, sort_grouped_people, relationship_priority

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


def _norm_candidate_value(value):
    return ''.join(str(value or '').strip().casefold().split())


def review_row_for_finding(db, person_id, finding):
    """Map stored external evidence deterministically to its review row."""
    from .ryerson_discovery_review import discoveries_for_person
    rows=list(discoveries_for_person(db,int(person_id)))
    if not rows:
        return None

    keys=set(finding.keys())
    evidence_id=finding["id"] if "id" in keys else None
    if evidence_id not in (None,""):
        wanted=f"ryerson:{evidence_id}"
        exact=[r for r in rows if str(r["external_record_key"] or "")==wanted]
        if len(exact)==1:
            return exact[0]

    event_date=str(finding["event_date"] or "").strip() if "event_date" in keys else ""
    pub_date=str(finding["publication_date"] or "").strip() if "publication_date" in keys else ""
    publication=str(finding["publication"] or "").strip() if "publication" in keys else ""
    event_type=str(finding["event_type"] or "").strip() if "event_type" in keys else ""
    event_n=_norm_candidate_value(event_date)
    pubdate_n=_norm_candidate_value(pub_date)
    publication_n=_norm_candidate_value(publication)
    type_n=_norm_candidate_value(event_type)

    scored=[]
    for row in rows:
        score=0
        fact=str(row["proposed_fact_key"] or "")
        fact_date=fact.split(":",1)[1] if ":" in fact else ""
        if event_n and _norm_candidate_value(fact_date)==event_n: score+=8
        record=_norm_candidate_value(row["external_record_key"])
        if event_n and event_n in record: score+=6
        if pubdate_n and pubdate_n in record: score+=5
        if publication_n and publication_n in record: score+=4
        if type_n and type_n in record: score+=2
        source_n=_norm_candidate_value(row["source_name"])
        finding_source=_norm_candidate_value(finding["source_name"] if "source_name" in keys else "")
        if finding_source and source_n==finding_source: score+=1
        scored.append((score,row))
    scored.sort(key=lambda x:(-x[0],x[1]["id"]))
    if scored and scored[0][0] > 0 and (len(scored)==1 or scored[0][0] > scored[1][0]):
        return scored[0][1]

    actionable=[r for r in rows if r["state"] in ("new","deferred")]
    if len(actionable)==1:
        return actionable[0]
    return None
def finding_impossible_for_person(db, person_id, finding):
    from .ryerson_discovery_assembly import _definite_date
    birth=_first_event(db,int(person_id),'Birth')
    birth_text=_row_value(birth,'date_text','event_date','date','date_value')
    keys=set(finding.keys())
    event_text=''
    for name in ('event_date','death_date','funeral_date'):
        if name in keys and finding[name]:
            event_text=str(finding[name]).strip()
            break
    birth_date=_definite_date(birth_text)
    event_date=_definite_date(event_text)
    return bool(birth_date and event_date and event_date < birth_date)


def render_finding_decision_controls(db, person_id, finding, return_path=None):
    row=review_row_for_finding(db,person_id,finding)
    if row is None:
        return ""
    return _decision_forms(row,return_path or f"/person/{int(person_id)}?tab=research")

def _candidate_date_value(finding):
    from .ryerson_discovery_assembly import _definite_date
    keys=set(finding.keys())
    for name in ("event_date","death_date","funeral_date"):
        if name in keys and finding[name]:
            parsed=_definite_date(finding[name])
            if parsed:
                return parsed
    return None


def sort_external_findings_recent_first(findings):
    def key(finding):
        d=_candidate_date_value(finding)
        return (d is None, -(d.toordinal()) if d else 0, -int(finding["id"] or 0))
    return sorted(list(findings or []),key=key)


def render_external_evidence_candidate(db, person_id, finding, return_path=None):
    return_path=return_path or f"/person/{int(person_id)}?tab=research"
    if finding_impossible_for_person(db,person_id,finding):
        return ""

    keys=set(finding.keys())
    source=str(finding["source_name"] or "Ryerson") if "source_name" in keys else "Ryerson"
    heading=(finding["source_record_name"] if "source_record_name" in keys else None) or (finding["event_type"] if "event_type" in keys else None) or (finding["evidence_type"] if "evidence_type" in keys else None) or "Ryerson candidate"
    event_type=str(finding["event_type"] or "") if "event_type" in keys else ""
    event_date=str(finding["event_date"] or "") if "event_date" in keys else ""
    publication=str(finding["publication"] or "") if "publication" in keys else ""
    publication_date=str(finding["publication_date"] or "") if "publication_date" in keys else ""
    details=str(finding["details"] or "") if "details" in keys else ""
    place_claim=str(finding["place_claim"] or "") if "place_claim" in keys else ""
    birth_claim=str(finding["birth_date_claim"] or "") if "birth_date_claim" in keys else ""
    reason=str(finding["match_reason"] or "") if "match_reason" in keys else ""
    score=finding["match_confidence"] if "match_confidence" in keys else None

    review=review_row_for_finding(db,person_id,finding)
    evidence_status=str(finding["review_status"] or "new") if "review_status" in keys else "new"
    out=["<div class='rc-evidence-candidate'><div class='rc-evidence-head'><div>"]
    out.append(f"<div class='small'>{escape(source)}{f' · Match {score}%' if score is not None else ''}</div>")
    out.append(f"<h3>{escape(str(heading))}</h3></div>")
    if review is not None:
        state=review["state"]
        label=STATE_LABELS.get(state,state)
        cls="good" if state in ("waiting_for_reunion","already_known","confirmed_complete") else "info" if state=="rejected" else "warn"
        out.append(f"<span class='badge {cls}'>{escape(label)}</span>")
    else:
        label=evidence_status.replace("_"," ").title()
        cls="good" if evidence_status=="accepted" else "info" if evidence_status=="rejected" else "warn"
        out.append(f"<span class='badge {cls}'>{escape(label)}</span>")
    out.append("</div>")

    facts=[]
    if event_type or event_date: facts.append(("Event"," ".join(x for x in (event_type,event_date) if x)))
    if publication: facts.append(("Publication",publication))
    if publication_date: facts.append(("Published",publication_date))
    if birth_claim: facts.append(("Birth claim",birth_claim))
    if place_claim: facts.append(("Place",place_claim))
    if facts:
        out.append("<div class='rc-evidence-facts'>")
        for label,value in facts:
            out.append(f"<div><span>{escape(label)}</span><strong>{escape(str(value))}</strong></div>")
        out.append("</div>")
    if details: out.append(f"<div class='rc-evidence-details'>{escape(details)}</div>")
    if reason: out.append(f"<div class='small rc-evidence-match'>Match basis: {escape(reason)}</div>")
    if review is not None:
        out.append("<div class='rc-evidence-actions'>"+_decision_forms(review,return_path)+"</div>")
    else:
        out.append("<div class='small rc-evidence-unlinked'>Review controls unavailable for this stored finding.</div>")
    out.append("</div>")
    return "".join(out)


def render_person_discovery_decisions(db, person_id, return_path=None):
    from .ryerson_discovery_review import discoveries_for_person
    rows=discoveries_for_person(db,int(person_id))
    if not rows:
        return ""
    return_path=return_path or f"/person/{int(person_id)}?tab=research"
    out=[
        "<div class='topic'><strong>Discovery decisions</strong>"
        "<div class='small'>Assess each candidate here. Decisions are saved by Companion and do not alter Reunion automatically.</div></div>"
    ]
    for row in rows:
        fact=row["proposed_fact_key"] or "Evidence candidate"
        state=row["state"]
        badge_class="good" if state in ("waiting_for_reunion","already_known","confirmed_complete") else "info" if state=="rejected" else "warn"
        out.append("<div class='result'>")
        out.append(f"<strong>{escape(fact)}</strong> <span class='badge {badge_class}'>{escape(STATE_LABELS.get(state,state))}</span>")
        out.append(f"<div class='small'>{escape(row['source_name'])}</div>")
        if row["decision_note"]:
            out.append(f"<div class='small'>{escape(row['decision_note'])}</div>")
        out.append(_decision_forms(row,return_path))
        out.append("</div>")
    return "".join(out)


def render_discovery_review_section(db, *, preview_people=5, focus_id=None):
    from .ryerson_discovery_review import discovery_counts
    counts=discovery_counts(db)
    focus=resolve_focus_person(db,focus_id)

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
        rels={}
        if focus:
            people,rels=sort_grouped_people(db,focus["id"],people)
        out.append(
            f"<p><a class='button' href='/research/discoveries?state=new&page=1'>Review New Discoveries</a> "
            f"<span class='small'>{counts['new']} discoveries across {len(people)} people</span></p>"
        )
        if focus:
            out.append(f"<div class='topic'><strong>Research focus: {escape(focus['display_name'])}</strong><div class='small'>Prioritised outward through the recorded family network.</div></div>")
        out.append("<h3>Next people to review</h3>")
        for person_id,candidates in people[:preview_people]:
            name=_person_name(candidates[0])
            relation=rels.get(int(person_id),{"label":"Relationship not established"})["label"]
            out.append(
                f"<a class='result' href='/person/{person_id}?tab=research'>"
                f"<strong>{escape(name)}</strong>"
                f"<span class='badge warn' style='float:right'>{len(candidates)} candidate{'s' if len(candidates)!=1 else ''}</span>"
                f"<span class='meta' style='display:block'>{escape(relation)}</span>"
                "</a>"
            )
        if len(people)>preview_people:
            out.append(f"<div class='small'>Showing {preview_people} of {len(people)} people with new discoveries.</div>")

    out.append("</div>")
    return "".join(out)


def render_discovery_workspace(db, *, state="new", page=1, page_size=20, person_id=None, focus_id=None):
    from .ryerson_discovery_review import discovery_counts

    if state not in STATE_ORDER:
        state="new"
    page=max(1,int(page or 1))
    page_size=max(1,min(100,int(page_size or 20)))

    rows=discovery_review_rows(db,state=state)
    people=_group_people(rows)
    focus=resolve_focus_person(db,focus_id)
    rels={}
    if focus:
        people,rels=sort_grouped_people(db,focus["id"],people)

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
    if focus:
        out.append(f"<div class='topic'><strong>Research focus: {escape(focus['display_name'])}</strong><div class='small'>Closest recorded family relationships are shown first.</div></div>")
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
        relation=rels.get(int(pid),relationship_priority(db,focus["id"],pid) if focus else {"label":"Relationship not established"})
        out.append("<div class='card'>")
        out.append(
            f"<h2><a href='/person/{pid}?tab=research'>{escape(context['name'])}</a> "
            f"<span class='small'>({len(candidates)} Ryerson candidate{'s' if len(candidates)!=1 else ''})</span></h2>"
        )
        out.append(f"<div class='meta'>{escape(relation['label'])}</div>")
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
