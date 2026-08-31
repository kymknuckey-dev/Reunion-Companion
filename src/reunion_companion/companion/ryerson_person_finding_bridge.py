from __future__ import annotations

from .ryerson_discovery_assembly import assemble_discoveries


def _get(item, *names, default=None):
    for name in names:
        try:
            value=item[name]
        except Exception:
            continue
        if value not in (None,""):
            return value
    return default


def _source_is_ryerson(item) -> bool:
    source=str(_get(item,"source_name","source","provider",default="")).casefold()
    return "ryerson" in source


def _finding_to_candidate(person_id, finding):
    if not _source_is_ryerson(finding):
        return None

    external_id=_get(
        finding,
        "external_record_key","notice_id","source_record_id","ryerson_id",
        "record_id","id",
    )
    if external_id in (None,""):
        name=_get(finding,"name","display_name","source_record_name",default="")
        event_date=_get(finding,"death_date","event_date",default="")
        publication_date=_get(finding,"publication_date","published_date",default="")
        publication=_get(finding,"publication","newspaper",default="")
        external_id=f"{name}|{event_date}|{publication_date}|{publication}"

    status=str(_get(finding,"review_status","match_status","status",default="candidate"))
    if status.casefold() in {"rejected","excluded","no_match","ambiguous"}:
        return None

    candidate={
        "person_id":person_id,
        "notice_id":str(external_id),
        "match_status":"candidate",
        "match_reason":str(_get(finding,"match_reason","reason",default="Existing person-level Ryerson finding")),
        "match_confidence":_get(finding,"match_confidence","confidence",default=None),
    }

    notice_type=str(_get(finding,"notice_type","evidence_type","type",default=""))
    event_type=str(_get(finding,"event_type",default=""))

    for target,names in {
        "surname":("surname","last_name"),
        "given_name":("given_name","first_name","given_names"),
        "funeral_date":("funeral_date",),
        "publication_date":("publication_date","published_date"),
        "newspaper":("newspaper","publication"),
        "notice_type":("notice_type","evidence_type","type"),
    }.items():
        value=_get(finding,*names)
        if value not in (None,""):
            candidate[target]=value

    # A Ryerson funeral notice commonly carries the notice/publication date in
    # event_date.  It is corroborating evidence for the death, not a second
    # death date to write back to Reunion.  Only death notices (or an explicit
    # death_date field) may propose a Reunion Death fact.
    explicit_death_date=_get(finding,"death_date",default=None)
    is_funeral_notice="funeral" in notice_type.casefold()
    if explicit_death_date not in (None,""):
        candidate["death_date"]=explicit_death_date
    elif not is_funeral_notice and event_type.casefold()=="death":
        event_date=_get(finding,"event_date",default=None)
        if event_date not in (None,""):
            candidate["death_date"]=event_date

    return candidate


def materialize_person_level_ryerson_findings(db, person_gedcom_xref=None):
    """Materialise stored Ryerson evidence into the person-level review index.

    With an xref, bridge only that person's findings. Without one, backfill all
    currently stored findings. The operation is idempotent and preserves prior
    review decisions.
    """
    from .external_evidence import external_evidence_for_person

    if person_gedcom_xref:
        people=db.execute(
            "SELECT id,gedcom_xref FROM people WHERE gedcom_xref=? ORDER BY id",
            (person_gedcom_xref,),
        ).fetchall()
    else:
        people=db.execute(
            "SELECT id,gedcom_xref FROM people "
            "WHERE gedcom_xref IS NOT NULL AND trim(gedcom_xref)<>'' "
            "ORDER BY id"
        ).fetchall()

    candidates=[]
    people_with_findings=0
    ryerson_findings=0

    for person in people:
        findings=external_evidence_for_person(db,person["gedcom_xref"]) or []
        if findings:
            people_with_findings+=1
        for finding in findings:
            candidate=_finding_to_candidate(person["id"],finding)
            if candidate is None:
                continue
            candidates.append(candidate)
            ryerson_findings+=1

    result=assemble_discoveries(db,candidates)
    return {
        "people_checked":len(people),
        "people_with_findings":people_with_findings,
        "ryerson_findings":ryerson_findings,
        "assembled_count":result["assembled_count"],
        "skipped_count":result["skipped_count"],
    }
