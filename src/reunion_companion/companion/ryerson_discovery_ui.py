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
    "ineligible": "No Longer Eligible",
}

STATE_ORDER = (
    "new",
    "waiting_for_reunion",
    "deferred",
    "already_known",
    "rejected",
    "confirmed_complete",
    "ineligible",
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
        f"<form method='post' action='/research/discovery/{rid}/waiting' style='display:inline-block;margin-right:.4rem'>{hidden}<button type='submit'>Accept</button></form>",
        f"<form method='post' action='/research/discovery/{rid}/known' style='display:inline-block;margin-right:.4rem'>{hidden}<button type='submit'>Known</button></form>",
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
    """Order review candidates by confidence first, then event-date recency.

    The historical function name is retained for compatibility with existing callers.
    """
    def key(finding):
        d=_candidate_date_value(finding)
        try:
            confidence=int(finding["match_confidence"] or 0)
        except (KeyError,TypeError,ValueError):
            confidence=0
        return (-confidence, d is None, -(d.toordinal()) if d else 0, -int(finding["id"] or 0))
    return sorted(list(findings or []),key=key)


def _evidence_icon(kind):
    if kind=="date":
        return "<svg class='rc-evidence-icon' viewBox='0 0 24 24' aria-hidden='true'><rect x='3.5' y='5.5' width='17' height='15' rx='2'/><path d='M7 3.5v4M17 3.5v4M3.5 9.5h17'/></svg>"
    if kind=="place":
        return "<svg class='rc-evidence-icon' viewBox='0 0 24 24' aria-hidden='true'><path d='M12 21s6-5.2 6-11a6 6 0 1 0-12 0c0 5.8 6 11 6 11z'/><circle cx='12' cy='10' r='2.2'/></svg>"
    return ""


def _candidate_summary(finding):
    keys=set(finding.keys())
    event_type=str(finding["event_type"] or "") if "event_type" in keys else ""
    event_date=str(finding["event_date"] or "") if "event_date" in keys else ""
    publication=str(finding["publication"] or "") if "publication" in keys else ""
    publication_date=str(finding["publication_date"] or "") if "publication_date" in keys else ""
    primary=" ".join(x for x in (event_type,event_date) if x).strip()
    bits=[primary] if primary else []
    if publication:
        bits.append(publication)
    if publication_date:
        bits.append("published "+publication_date)
    return " · ".join(bits) or "Ryerson candidate"


def render_external_evidence_candidate(db, person_id, finding, return_path=None):
    return_path=return_path or f"/person/{int(person_id)}?tab=research"
    if finding_impossible_for_person(db,person_id,finding):
        return ""

    keys=set(finding.keys())
    source=str(finding["source_name"] or "Ryerson") if "source_name" in keys else "Ryerson"
    record_name=str(finding["source_record_name"] or "") if "source_record_name" in keys else ""
    event_type=str(finding["event_type"] or "") if "event_type" in keys else ""
    event_date=str(finding["event_date"] or "") if "event_date" in keys else ""
    details=str(finding["details"] or "") if "details" in keys else ""
    place_claim=str(finding["place_claim"] or "") if "place_claim" in keys else ""
    reason=str(finding["match_reason"] or "") if "match_reason" in keys else ""
    score=finding["match_confidence"] if "match_confidence" in keys else None
    summary=_candidate_summary(finding)

    review=review_row_for_finding(db,person_id,finding)
    evidence_status=str(finding["review_status"] or "new") if "review_status" in keys else "new"
    from .ryerson_discovery_assembly import _definite_date
    sort_date=_definite_date(event_date)
    sort_value=sort_date.toordinal() if sort_date else 0

    out=[f"<article class='rc-evidence-candidate' data-event-sort='{sort_value}' data-confidence='{int(score or 0)}'>"]

    out.append("<section class='rc-evidence-primary'>")
    out.append(f"<div class='rc-evidence-source'>{escape(source)}{f' · Match {score}%' if score is not None else ''}</div>")
    if record_name:
        out.append(f"<div class='rc-evidence-record-name'>{escape(record_name)}</div>")
    out.append(f"<div class='rc-evidence-summary'>{escape(summary)}</div>")
    if details:
        out.append(f"<div class='rc-evidence-details'>{escape(details)}</div>")
    if reason:
        out.append(f"<div class='rc-evidence-match'>Match basis: {escape(reason)}</div>")
    out.append("</section>")

    out.append("<section class='rc-evidence-context'>")
    if event_date:
        out.append("<div class='rc-evidence-context-row'>"+_evidence_icon("date")+f"<span>{escape(event_date)}</span></div>")
    if place_claim:
        out.append("<div class='rc-evidence-context-row'>"+_evidence_icon("place")+f"<span>{escape(place_claim)}</span></div>")
    if event_type:
        out.append(f"<div class='rc-evidence-event-type'>Event type: <strong>{escape(event_type)}</strong></div>")
    out.append("</section>")

    out.append("<section class='rc-evidence-decision'>")
    out.append("<div class='rc-chronology-ok'>✓ Chronology OK</div>")

    if review is not None:
        state=review["state"]
        if state not in ("new","deferred"):
            label=STATE_LABELS.get(state,state)
            cls="good" if state in ("waiting_for_reunion","already_known","confirmed_complete") else "info" if state=="rejected" else "warn"
            out.append(f"<div class='rc-evidence-state'><span class='badge {cls}'>{escape(label)}</span></div>")
        out.append("<div class='rc-evidence-actions'>"+_decision_forms(review,return_path)+"</div>")
    else:
        label=evidence_status.replace("_"," ").title()
        cls="good" if evidence_status=="accepted" else "info" if evidence_status=="rejected" else "warn"
        out.append(f"<div class='rc-evidence-state'><span class='badge {cls}'>{escape(label)}</span></div>")
        out.append("<div class='rc-evidence-unlinked'>Review controls unavailable for this stored finding.</div>")

    out.append("</section>")
    out.append("</article>")
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


def _review_fact_date(row):
    from .ryerson_discovery_assembly import _definite_date
    fact=str(row["proposed_fact_key"] or "")
    if ":" not in fact:
        return None
    _,raw=fact.split(":",1)
    return _definite_date(raw)


def _group_recent_date(candidates):
    dates=[d for d in (_review_fact_date(r) for r in candidates) if d is not None]
    return max(dates) if dates else None


def _person_new_evidence_confidence(db, person_id):
    """Highest confidence among this person's currently new external evidence."""
    try:
        row=db.execute(
            "SELECT MAX(CAST(e.match_confidence AS INTEGER)) AS confidence "
            "FROM companion_external_evidence e "
            "JOIN people p ON p.gedcom_xref=e.person_gedcom_xref "
            "WHERE p.id=? AND COALESCE(e.review_status,'new')='new'",
            (int(person_id),),
        ).fetchone()
        return int(row["confidence"] or 0) if row else 0
    except Exception:
        return 0


def _group_match_confidence(candidates):
    values=[]
    for row in candidates:
        try:
            value=row["match_confidence"]
        except (KeyError, IndexError, TypeError):
            value=None
        if value in (None, ""):
            continue
        try:
            values.append(int(float(value)))
        except (TypeError, ValueError):
            continue
    return max(values) if values else None


def sort_grouped_people_recent(grouped, db=None):
    """Review priority: highest unresolved candidate confidence, then newest candidate.

    The durable review index can lag a newly rescored external-evidence row.
    When a database is available, compare both sources and use the strongest
    currently unresolved candidate so a live 100%/95% match cannot sit below a
    stale lower-confidence review-index value.
    """
    def key(item):
        d=_group_recent_date(item[1])
        indexed_confidence=_group_match_confidence(item[1]) or 0
        live_confidence=_person_new_evidence_confidence(db,item[0]) if db is not None else 0
        confidence=max(indexed_confidence,live_confidence)
        return (-confidence,d is None,-d.toordinal() if d else 0,_person_name(item[1][0]).casefold(),int(item[0]))
    return sorted(grouped,key=key)


def _format_review_date(value):
    return value.strftime("%-d %b %Y") if value else "Date not available"



def _unsourced_death_rows(db, person_id):
    return db.execute(
        """
        SELECT e.id,e.date_text
        FROM events e
        WHERE e.person_id=? AND lower(e.event_type)='death'
          AND NOT EXISTS(SELECT 1 FROM event_sources es WHERE es.event_id=e.id)
          AND NOT EXISTS(SELECT 1 FROM event_media em WHERE em.event_id=e.id)
        ORDER BY e.id
        """,
        (int(person_id),),
    ).fetchall()


def _linked_ryerson_evidence(db, row):
    key=str(row["external_record_key"] or "")
    if str(row["source_name"] or "").casefold() != "ryerson" or not key.startswith("ryerson:"):
        return None
    raw=key.split(":",1)[1]
    if not raw.isdigit():
        return None
    return db.execute(
        "SELECT evidence_type,event_type,event_date,publication,publication_date,birth_date_claim,place_claim,details,match_confidence,match_reason FROM companion_external_evidence WHERE id=?",
        (int(raw),),
    ).fetchone()


def research_value_assessment(db, person_id, candidates):
    """Explain the best *currently new* research opportunity for one person.

    Research Value is deliberately read-only and candidate-specific.  It rewards
    evidence that can improve current Reunion data, while reducing the priority
    of broad/ambiguous name matches and very old missing-fact leads.
    """
    from datetime import date
    from .ryerson_discovery_assembly import _definite_date

    active=list(candidates)
    candidate_count=len(active)
    deaths=_unsourced_death_rows(db,person_id)
    death_dates=[(_definite_date(r["date_text"]),str(r["date_text"] or "")) for r in deaths]
    definite_existing=[d for d,_ in death_dates if d is not None]
    has_unsourced=bool(deaths)
    has_any_death=db.execute(
        "SELECT 1 FROM events WHERE person_id=? AND lower(event_type)='death' LIMIT 1",
        (int(person_id),),
    ).fetchone() is not None

    matching=[]
    missing_death=[]
    conflicting=[]
    plausible=[]
    for row in active:
        fact=str(row["proposed_fact_key"] or "").strip()
        evidence=_linked_ryerson_evidence(db,row)
        evidence_type=str(evidence["evidence_type"] or "").casefold() if evidence else ""
        event_type=str(evidence["event_type"] or "").casefold() if evidence else ""
        is_death_evidence=(event_type=="death" and "funeral" not in evidence_type)
        proposed=None
        if fact.casefold().startswith("death:"):
            proposed=_definite_date(fact.split(":",1)[1])
        if proposed is not None and is_death_evidence:
            if proposed in definite_existing and has_unsourced:
                matching.append((proposed,row))
            elif definite_existing and proposed not in definite_existing:
                conflicting.append((proposed,row))
            elif not has_any_death:
                missing_death.append((proposed,row))
            else:
                plausible.append(row)
        elif evidence is not None:
            plausible.append(row)

    # A definite candidate that agrees with an existing unsourced Death is the
    # strongest actionable case.  The exact-date agreement itself provides the
    # specificity, even when secondary publication rows also exist.
    if matching:
        d,_=max(matching,key=lambda item:item[0])
        return {"rank":0,"order":0,"level":"High opportunity","reason":"May source existing Death","detail":f"Reunion Death {_format_review_date(d)} · Ryerson Death {_format_review_date(d)} · dates agree"}

    # A missing Death is useful only when the candidate set is sufficiently
    # specific.  Broad common-name result sets must not be labelled High merely
    # because one candidate happens to be a Death record.
    if missing_death:
        d,_=max(missing_death,key=lambda item:item[0])
        age=max(0,date.today().year-d.year)
        if age <= 100 and candidate_count <= 2:
            return {"rank":0,"order":1,"level":"High opportunity","reason":"May fill missing Death","detail":f"Ryerson Death {_format_review_date(d)} · {candidate_count} current candidate{'s' if candidate_count != 1 else ''}"}
        if age <= 100 and candidate_count <= 5:
            return {"rank":1,"order":0,"level":"Potential opportunity","reason":"Missing Death has several possible matches","detail":f"Ryerson Death {_format_review_date(d)} · {candidate_count} current candidates"}
        if age > 100 and candidate_count <= 2:
            return {"rank":1,"order":1,"level":"Potential opportunity","reason":"Older missing Death lead","detail":f"Ryerson Death {_format_review_date(d)} · more than 100 years ago"}
        if age <= 100:
            return {"rank":2,"order":1,"level":"Needs careful review","reason":"Many possible Ryerson Death matches","detail":f"{candidate_count} current candidates · newest Death {_format_review_date(d)}"}
        return {"rank":3,"order":1,"level":"Lower immediate value","reason":"Old and highly ambiguous Death lead","detail":f"{candidate_count} current candidates · Ryerson Death {_format_review_date(d)}"}

    if conflicting:
        d,_=max(conflicting,key=lambda item:item[0])
        current=_format_review_date(definite_existing[0]) if definite_existing else "recorded date"
        return {"rank":2,"order":0,"level":"Needs careful review","reason":"Candidate Death conflicts with Reunion","detail":f"Reunion Death {current} · candidate Death {_format_review_date(d)}"}
    if has_unsourced and plausible:
        return {"rank":1,"order":2,"level":"Potential opportunity","reason":"New evidence may add to an unsourced Death","detail":"No new candidate directly confirms the recorded Death date"}
    if plausible:
        if candidate_count > 5:
            return {"rank":2,"order":2,"level":"Needs careful review","reason":"Broad candidate set needs disambiguation","detail":f"{candidate_count} current candidates · no specific Reunion gap yet confirmed"}
        return {"rank":1,"order":3,"level":"Potential opportunity","reason":"New evidence may add useful context","detail":"Review the current candidate evidence for possible additions"}
    return {"rank":3,"order":2,"level":"Lower immediate value","reason":"No obvious current Reunion gap identified","detail":"Current new candidates do not directly strengthen a detected Death gap"}


def sort_grouped_people_research_value(grouped, db):
    def key(item):
        assessment=research_value_assessment(db,item[0],item[1])
        confidence=_group_match_confidence(item[1]) or 0
        d=_group_recent_date(item[1])
        return (assessment["rank"],assessment.get("order",0),len(item[1]),-confidence,d is None,-d.toordinal() if d else 0,_person_name(item[1][0]).casefold(),int(item[0]))
    return sorted(grouped,key=key)

def discovery_match_assessment(db, person_id, candidates):
    """Summarise how strongly the supplied Ryerson review candidates identify a person.

    The caller supplies candidates for the active review state (New, Waiting for
    Reunion, Confirmed Complete, and so on). Candidate-specific evidence wins over
    person-level ambiguity.  Birth-date
    agreement is determined directly from the current Reunion Birth event and the
    Ryerson birth-date claim where possible, with the stored matcher reason retained
    as a compatibility fallback.
    """
    from .ryerson_discovery_assembly import _definite_date

    birth_rows=db.execute(
        "SELECT date_text FROM events WHERE person_id=? AND lower(event_type)='birth' ORDER BY id",
        (int(person_id),),
    ).fetchall()
    reunion_birth_dates={d for d in (_definite_date(r["date_text"]) for r in birth_rows) if d is not None}

    active=list(candidates)
    assessed=[]
    for row in active:
        evidence=_linked_ryerson_evidence(db,row)
        if evidence is None:
            continue
        reason=str(evidence["match_reason"] or "").casefold()
        confidence=int(evidence["match_confidence"] or row["match_confidence"] or 0)
        claim=_definite_date(str(evidence["birth_date_claim"] or ""))
        direct_birth_exact=claim is not None and claim in reunion_birth_dates
        birth_exact=direct_birth_exact or "birth date exact" in reason
        place_consistent="place consistent" in reason
        family=[]
        for label in ("spouse","child","parent"):
            if f"{label} corroborated" in reason:
                family.append(label)
        assessed.append((birth_exact,place_consistent,bool(family),confidence,evidence,row,family))

    count=len(active)
    if not assessed:
        return {"rank":3,"level":"Unassessed","reason":"No linked Ryerson match detail","detail":f"{count} current candidate{'s' if count != 1 else ''}"}

    # Candidate-specific evidence wins over person-level ambiguity.  A person may
    # have dozens of name candidates but still contain one exact birth-date match.
    best=max(assessed,key=lambda x:(x[0],x[1] or x[2],x[3]))
    birth_exact,place_consistent,family_supported,confidence,evidence,row,family=best
    publication=str(evidence["publication"] or "").strip()

    supports=[]
    if birth_exact:
        supports.append("Birth date agrees")
    if place_consistent:
        supports.append("Place agrees")
    if family_supported:
        supports.append("Family detail agrees")
    if publication:
        supports.append(f"Published in {publication}")

    strong_count=sum(1 for x in assessed if x[0])
    supported_count=sum(1 for x in assessed if (not x[0]) and (x[1] or x[2]) and x[3] >= 55)

    if birth_exact:
        prefix=(f"{strong_count} strong match{'es' if strong_count != 1 else ''} among {count}" if count > 1 else "Birth date identifies this candidate strongly")
        detail=" · ".join([prefix]+supports)
        return {"rank":0,"level":"Strong match","reason":"Birth date agrees","detail":detail}

    if (place_consistent or family_supported) and confidence >= 55:
        prefix=(f"{supported_count or 1} supported match{'es' if (supported_count or 1) != 1 else ''} among {count}" if count > 1 else "Supporting identity detail agrees")
        detail=" · ".join([prefix]+supports)
        return {"rank":1,"level":"Supported match","reason":"Supporting details agree","detail":detail}

    if count > 5:
        detail=f"{count} current candidates · name evidence only"
        if publication:
            detail+=f" · Best candidate published in {publication}"
        return {"rank":3,"level":"Low specificity","reason":"Many name-based candidates","detail":detail}

    detail=f"{count} current candidate{'s' if count != 1 else ''} · no birth-date or other identity corroboration yet"
    if publication:
        detail+=f" · Published in {publication}"
    return {"rank":2,"level":"Possible match","reason":"Name match needs confirmation","detail":detail}


def _match_grade_badge(assessment):
    level=assessment.get("level","")
    cls="good" if level=="Strong match" else "info" if level=="Supported match" else "warn"
    return f"<span class='badge {cls}' style='float:right'>{escape(level)}</span>"


def _review_sort_controls(people, *, sort_mode, focus):
    options={}
    if focus:
        options[int(focus["id"])]=str(focus["display_name"])
    for pid,candidates in people:
        options[int(pid)]=_person_name(candidates[0])
    current=int(focus["id"]) if focus else None
    opts=[]
    for pid,name in sorted(options.items(),key=lambda x:x[1].casefold()):
        selected=" selected" if current==pid else ""
        opts.append(f"<option value='{pid}'{selected}>{escape(name)}</option>")
    recent_active=" active" if sort_mode=="recent" else ""
    relationship_active=" active" if sort_mode=="relationship" else ""
    relationship_href="/research?sort=relationship"+(f"&focus={current}" if current else "")
    return (
        "<div class='rc-review-sortbar'>"
        "<div class='rc-review-sortchoices'>"
        f"<a class='rc-review-sortchoice{recent_active}' href='/research?sort=recent'>Most Recent</a>"
        f"<a class='rc-review-sortchoice{relationship_active}' id='rc-relationship-sort' href='{relationship_href}'>Relationship</a>"
        "</div>"
        "<form class='rc-review-anchor-form' method='get' action='/research'>"
        "<input type='hidden' name='sort' value='relationship'>"
        "<label><span>Relationship anchor</span>"
        f"<select name='focus'>{''.join(opts)}</select></label>"
        "<button type='submit'>Use Anchor</button>"
        "</form>"
        "<div id='rc-relationship-loading' class='rc-review-loading' style='display:none'>"
        "<span class='rc-review-spinner' aria-hidden='true'></span>Calculating relationships…</div>"
        "<script>(function(){var a=document.getElementById('rc-relationship-sort');var f=document.querySelector('.rc-review-anchor-form');var l=document.getElementById('rc-relationship-loading');function show(){if(l)l.style.display='inline-flex';}if(a)a.addEventListener('click',show);if(f)f.addEventListener('submit',show);})();</script>"
        "</div>"
    )


def render_discovery_review_section(db, *, preview_people=12, focus_id=None, sort_mode="recent", page=1, group=None):
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
        out.append("</div>")
        return "".join(out)

    rows=discovery_review_rows(db,state="new")
    people=_group_people(rows)
    sort_mode="relationship" if sort_mode=="relationship" else "recent"
    rels={}
    if sort_mode=="relationship" and focus:
        people,rels=sort_grouped_people(db,focus["id"],people)
    else:
        people=sort_grouped_people_recent(people,db)

    href=f"/research/discoveries?state=new&page=1&sort={sort_mode}"+(f"&focus={focus['id']}" if focus else "")
    out.append(f"<p><a class='button' href='{href}'>Review New Discoveries</a> <span class='small'>{counts['new']} discoveries across {len(people)} people</span></p>")
    out.append(_review_sort_controls(people,sort_mode=sort_mode,focus=focus))
    if sort_mode=="relationship" and focus:
        out.append(f"<div class='topic'><strong>Grouped by match quality</strong><div class='small'>Within each group, closest recorded family relationships to {escape(focus['display_name'])} are shown first.</div></div>")
    else:
        out.append("<div class='topic'><strong>Grouped by match quality</strong><div class='small'>Strong identity matches are separated from less specific candidates. Within each group, the newest candidate date appears first.</div></div>")

    grade_order=("Strong match","Supported match","Possible match","Low specificity","Unassessed")
    grade_slug={"Strong match":"strong","Supported match":"supported","Possible match":"possible","Low specificity":"low","Unassessed":"unassessed"}
    grade_help={
        "Strong match":"Birth date agrees with Reunion.",
        "Supported match":"Place or family detail supports the identity.",
        "Possible match":"Name match still needs confirmation.",
        "Low specificity":"Broad name-based candidate set with little identity corroboration.",
        "Unassessed":"Linked Ryerson identity detail is not available.",
    }
    grouped={name:[] for name in grade_order}
    assessments={}
    for pid,candidates in people:
        assessment=discovery_match_assessment(db,pid,candidates)
        assessments[int(pid)]=assessment
        grouped.setdefault(assessment.get("level","Unassessed"),[]).append((pid,candidates))

    requested_slug=str(group or "").strip().casefold()
    if requested_slug not in set(grade_slug.values()):
        requested_slug="strong" if grouped.get("Strong match") else next((grade_slug[g] for g in grade_order if grouped.get(g)),"")

    for level in grade_order:
        members=grouped.get(level,[])
        if not members:
            continue
        slug=grade_slug[level]
        group_page=page if slug==requested_slug else 1
        total=len(members)
        pages=max(1,(total+preview_people-1)//preview_people)
        group_page=max(1,min(group_page,pages))
        start=(group_page-1)*preview_people
        shown=members[start:start+preview_people]
        open_attr=" open" if slug==requested_slug else ""
        out.append(f"<details class='rc-review-grade-group' id='preview-grade-{slug}'{open_attr}>")
        out.append(f"<summary class='rc-review-grade-summary'><span><strong>{escape(level)}</strong> <span class='badge'>{total} people</span></span><span class='small'>{escape(grade_help[level])}</span></summary>")
        out.append("<div class='rc-review-person-list'>")
        for person_id,candidates in shown:
            name=_person_name(candidates[0])
            grade=assessments[int(person_id)]
            context=(rels.get(int(person_id),{"label":"Relationship not established"})["label"] if sort_mode=="relationship" else "Most recent candidate: "+_format_review_date(_group_recent_date(candidates)))
            count=len(candidates)
            detail=f"{grade['detail']} · {count} candidate{'s' if count!=1 else ''} · {context}"
            out.append(f"<a class='result' href='/person/{person_id}?tab=research'><strong>{escape(name)}</strong>{_match_grade_badge(grade)}<span class='meta' style='display:block'>{escape(detail)}</span></a>")
        out.append("</div>")
        if pages>1:
            keep=f"sort={quote(sort_mode)}&evidence_group={quote(slug)}"+(f"&focus={focus['id']}" if focus else "")
            nav=[]
            if group_page>1:
                nav.append(f"<a class='button' href='/research?{keep}&evidence_page={group_page-1}#preview-grade-{slug}'>Previous</a>")
            nav.append(f"<span class='small'>Page {group_page} of {pages} · {total} people in {escape(level)}</span>")
            if group_page<pages:
                nav.append(f"<a class='button' href='/research?{keep}&evidence_page={group_page+1}#preview-grade-{slug}'>Next</a>")
            out.append("<div class='rc-priority-pager'>"+" ".join(nav)+"</div>")
        out.append("</details>")

    out.append("</div>")
    return "".join(out)

def render_discovery_workspace(db, *, state="new", page=1, page_size=20, person_id=None, focus_id=None, sort_mode="recent", group=None):
    from .ryerson_discovery_review import discovery_counts

    if state not in STATE_ORDER:
        state="new"
    page=max(1,int(page or 1))
    page_size=max(1,min(100,int(page_size or 20)))

    rows=discovery_review_rows(db,state=state)
    people=_group_people(rows)
    focus=resolve_focus_person(db,focus_id)
    sort_mode="relationship" if sort_mode=="relationship" else "recent"
    rels={}
    if sort_mode=="relationship" and focus:
        people,rels=sort_grouped_people(db,focus["id"],people)
    else:
        people=sort_grouped_people_recent(people,db)

    if person_id is not None:
        people=[item for item in people if int(item[0])==int(person_id)]
        page=1

    out=[
        "<h1>External Evidence Review</h1>",
        "<p class='meta'>Browse Ryerson discoveries by review state. Open a person to review candidates with the full Reunion and external-evidence context.</p>",
        "<div class='card'>",
        "<div class='topic'><strong>Review state</strong>",
    ]
    counts=discovery_counts(db)
    links=[]
    for key in STATE_ORDER:
        if key=="ineligible":
            continue
        href=f"/research/discoveries?state={quote(key)}&page=1&sort={quote(sort_mode)}"+(f"&focus={focus['id']}" if focus else "")
        active=" active" if key==state else ""
        links.append(f"<a class='rc-review-statechoice{active}' href='{href}'>{escape(STATE_LABELS[key])} <span>{counts[key]}</span></a>")
    out.append("<div class='rc-review-statebar'>"+"".join(links)+"</div></div>")
    out.append(_review_sort_controls(people,sort_mode=sort_mode,focus=focus))
    if sort_mode=="relationship" and focus:
        out.append(f"<div class='topic'><strong>Relationship anchor: {escape(focus['display_name'])}</strong><div class='small'>Grouped by match quality; within each group, closest recorded family relationships are shown first.</div></div>")
    else:
        out.append("<div class='topic'><strong>Grouped by match quality</strong><div class='small'>Strong identity matches are separated from less specific candidates. Within each group, the newest candidate event date appears first.</div></div>")
    state_summary=(f"{len(people)} people in this review state" if state=="ineligible" else f"{len(people)} people with {STATE_LABELS.get(state,state)} discoveries")
    out.append(f"<div class='small rc-review-page-summary'>{escape(state_summary)}</div>")
    out.append("</div>")

    if not people:
        out.append("<div class='card'><p>No discoveries in this review state.</p></div>")
        return "".join(out)

    grade_order=("Strong match","Supported match","Possible match","Low specificity","Unassessed")
    grade_slug={
        "Strong match":"strong",
        "Supported match":"supported",
        "Possible match":"possible",
        "Low specificity":"low",
        "Unassessed":"unassessed",
    }
    grade_help={
        "Strong match":"Birth date agrees with Reunion.",
        "Supported match":"Place or family detail supports the identity.",
        "Possible match":"Name match still needs confirmation.",
        "Low specificity":"Broad name-based candidate set with little identity corroboration.",
        "Unassessed":"Linked Ryerson identity detail is not available.",
    }
    grouped={name:[] for name in grade_order}
    assessments={}
    for pid,candidates in people:
        grade=discovery_match_assessment(db,pid,candidates)
        assessments[int(pid)]=grade
        grouped.setdefault(grade.get("level","Unassessed"),[]).append((pid,candidates))

    requested_slug=str(group or "").strip().casefold()
    known_slugs=set(grade_slug.values())
    if requested_slug not in known_slugs:
        requested_slug="strong" if grouped.get("Strong match") else next((grade_slug[g] for g in grade_order if grouped.get(g)),"")

    # Page belongs to the explicitly selected/expanded grade.  Other groups stay
    # on their first page, so Previous/Next lives inside the group it controls.
    for level in grade_order:
        members=grouped.get(level,[])
        if not members:
            continue
        slug=grade_slug[level]
        group_page=page if slug==requested_slug else 1
        total=len(members)
        total_pages=max(1,(total+page_size-1)//page_size)
        group_page=max(1,min(group_page,total_pages))
        start=(group_page-1)*page_size
        shown=members[start:start+page_size]
        is_open=(slug==requested_slug)
        open_attr=" open" if is_open else ""
        out.append(f"<details class='card rc-review-grade-group' id='grade-{slug}'{open_attr}>")
        out.append(
            f"<summary class='rc-review-grade-summary'><span><strong>{escape(level)}</strong> "
            f"<span class='badge'>{total} people</span></span>"
            f"<span class='small'>{escape(grade_help[level])}</span></summary>"
        )
        out.append("<div class='rc-review-person-list'>")
        for pid,candidates in shown:
            context=person_reunion_context(db,pid)
            grade=assessments[int(pid)]
            if sort_mode=="relationship":
                relation=rels.get(int(pid),{"label":"Relationship not established"})
            else:
                relation={"label":"Most recent candidate: "+_format_review_date(_group_recent_date(candidates))}
            count=len(candidates)
            bits=[]
            if context.get("birth"):
                bits.append(f"Birth: {context['birth']}")
            if context.get("death"):
                bits.append(f"Death: {context['death']}")
            bits.append(grade['detail'])
            bits.append(f"{count} candidate{'s' if count!=1 else ''}")
            if relation.get("label"):
                bits.append(relation["label"])
            summary=" · ".join(bits)
            out.append(
                f"<a class='result rc-review-person-summary' href='/person/{pid}?tab=research'>"
                f"<span class='rc-review-person-main'><strong>{escape(context['name'])}</strong>"
                f"<span class='small'>{escape(summary)}</span></span>"
                f"{_match_grade_badge(grade)}"
                "</a>"
            )
        out.append("</div>")

        workspace_pager=""
        if total_pages>1:
            suffix=f"&sort={quote(sort_mode)}&group={quote(slug)}"+(f"&focus={focus['id']}" if focus else "")
            nav=[]
            if group_page>1:
                nav.append(f"<a class='button' href='/research/discoveries?state={quote(state)}&page={group_page-1}{suffix}#grade-{slug}'>Previous</a>")
            nav.append(f"<span class='small'>Page {group_page} of {total_pages} · {total} people in {escape(level)}</span>")
            if group_page<total_pages:
                nav.append(f"<a class='button' href='/research/discoveries?state={quote(state)}&page={group_page+1}{suffix}#grade-{slug}'>Next</a>")
            workspace_pager="<div class='rc-priority-pager'>"+" ".join(nav)+"</div>"
        shown_count=len(shown)
        if total_pages>1:
            out.append(f"<div class='small rc-review-group-count'>Showing {shown_count} of {total} people in {escape(level)}</div>")
        elif total>0:
            out.append(f"<div class='small rc-review-group-count'>{total} people in {escape(level)}</div>")
        if workspace_pager:
            out.append(workspace_pager)
        out.append("</details>")

    return "".join(out)
