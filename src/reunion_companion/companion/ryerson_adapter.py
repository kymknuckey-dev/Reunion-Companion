"""Ryerson Index source adapter.

RC1.0.14.5.1 deliberately separates source semantics from live HTTP transport.
The live probe can therefore change request mechanics without changing parsing,
normalisation, matching, queueing or review behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
import re

from .external_evidence_scan import SourceBusyError, SourceSearchError


RYERSON_SOURCE = "Ryerson"
DEFAULT_STATE = ""


@dataclass(frozen=True)
class RyersonQuery:
    surname: str
    given_names: str
    state: str = DEFAULT_STATE


def _clean(value: str | None) -> str:
    return " ".join((value or "").split())


def build_ryerson_queries(profile: dict, state: str = DEFAULT_STATE) -> list[RyersonQuery]:
    """Build the single Ryerson retrieval query for a Reunion person.

    Retrieval intentionally uses surname plus the first recorded given name
    only. Middle and later given names remain available to downstream candidate
    matching, where they are useful evidence, without causing an extra Ryerson
    request before a first-name fallback.
    """
    surname=_clean(profile.get("surname"))
    if len(surname) < 2:
        return []

    given=_clean(profile.get("given_names"))
    first=given.split()[0] if given else ""
    return [RyersonQuery(surname=surname,given_names=first,state=state)]


def logical_form_payload(query: RyersonQuery) -> dict:
    """Return source-semantic fields, not yet site-specific HTML input names.

    RC1.0.14.5.2 will map these logical fields to the live form after probing
    the request contract from the user's Mac.
    """
    return {
        "surname": query.surname,
        "given_names": query.given_names,
        "state": query.state,
    }


class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_cell=False
        self.cell_parts=[]
        self.row=[]
        self.rows=[]

    def handle_starttag(self, tag, attrs):
        if tag.lower() in ("td","th"):
            self.in_cell=True
            self.cell_parts=[]

    def handle_data(self, data):
        if self.in_cell:
            self.cell_parts.append(data)

    def handle_endtag(self, tag):
        tag=tag.lower()
        if tag in ("td","th") and self.in_cell:
            self.row.append(_clean(" ".join(self.cell_parts)))
            self.in_cell=False
            self.cell_parts=[]
        elif tag=="tr":
            if self.row:
                self.rows.append(self.row)
            self.row=[]


def _header_key(text: str) -> str:
    t=re.sub(r"[^a-z0-9]+"," ",text.casefold()).strip()
    aliases={
        "surname":"surname",
        "given names":"given_names",
        "given name":"given_names",
        "notice type":"notice_type",
        "date":"date",
        "event":"event",
        "age":"age",
        "other details":"other_details",
        "publication":"publication",
        "published":"published",
    }
    return aliases.get(t,t.replace(" ","_"))


def parse_ryerson_results(html: str) -> list[dict]:
    parser=_TableParser()
    parser.feed(html or "")
    rows=parser.rows
    if not rows:
        return []

    header_index=None
    keys=[]
    for i,row in enumerate(rows):
        mapped=[_header_key(x) for x in row]
        if "surname" in mapped and "given_names" in mapped:
            header_index=i
            keys=mapped
            break
    if header_index is None:
        return []

    results=[]
    for row in rows[header_index+1:]:
        if len(row)<2:
            continue
        values=dict(zip(keys,row))
        surname=_clean(values.get("surname"))
        given=_clean(values.get("given_names"))
        if not surname and not given:
            continue

        notice=_clean(values.get("notice_type"))
        event=_clean(values.get("event"))
        event_date=_clean(values.get("date"))
        details=_clean(values.get("other_details"))
        publication=_clean(values.get("publication"))
        published=_clean(values.get("published"))
        age=_clean(values.get("age"))

        source_name=" ".join(x for x in (given,surname) if x)
        evidence_type="funeral_notice" if "funeral" in notice.casefold() else "death_notice"
        if notice and "death" not in notice.casefold() and "funeral" not in notice.casefold():
            evidence_type=re.sub(r"[^a-z0-9]+","_",notice.casefold()).strip("_") or "notice"

        birth_claim=None
        m=re.search(
            r"\bborn\s+(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})",
            details,
            flags=re.I,
        )
        if m:
            birth_claim=_clean(m.group(1))

        place_claim=None
        m=re.search(r"\blate of\s+([^()]+?)(?:\s*\(|$)",details,flags=re.I)
        if m:
            place_claim=_clean(m.group(1)).strip(" ,.;")

        normalised={
            "evidence_type":evidence_type,
            "source_record_name":source_name,
            "event_type":event or ("Funeral" if evidence_type=="funeral_notice" else "Death"),
            "event_date":event_date or None,
            "publication":publication or None,
            "publication_date":published or None,
            "details":details or None,
            "birth_date_claim":birth_claim,
            "place_claim":place_claim,
        }
        if age:
            normalised["age_claim"]=age
        results.append(normalised)
    return results


def response_is_busy(status_code: int, body: str | None) -> bool:
    if int(status_code or 0)==429:
        return True
    low=(body or "").casefold()
    phrases=(
        "server is busy",
        "server busy",
        "try again later",
        "too many requests",
        "temporarily unavailable",
    )
    return any(p in low for p in phrases)


def response_is_success(status_code: int) -> bool:
    return 200 <= int(status_code or 0) < 300


def search_ryerson(profile: dict, fetch_fn, state: str = DEFAULT_STATE) -> list[dict]:
    """Search Ryerson through an injected transport.

    fetch_fn(query) must return (status_code, html_body). A busy response raises
    SourceBusyError so the unattended queue can back off and retry later.
    """
    queries=build_ryerson_queries(profile,state)
    if not queries:
        return []

    last_error=None
    for query in queries:
        status,body=fetch_fn(query)
        if response_is_busy(status,body):
            raise SourceBusyError("Ryerson server busy; try again later")
        if not response_is_success(status):
            last_error=f"Ryerson HTTP {status}"
            continue
        results=parse_ryerson_results(body)
        if results:
            return results

    if last_error:
        raise SourceSearchError(last_error)
    return []


def make_ryerson_search(fetch_fn, state: str = DEFAULT_STATE):
    """Return the callable expected by external_evidence_scan.run_one_scan."""
    def _search(profile):
        return search_ryerson(profile,fetch_fn,state=state)
    return _search
