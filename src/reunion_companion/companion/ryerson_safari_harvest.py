"""Safari annual/location harvest for Ryerson.

RC1.0.14.7.1 drives the live Ryerson search form through Safari, parses each
results page with the existing Ryerson parser, stores notices in the 14.7 cache,
and follows ordinary pagination links conservatively.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import time
from urllib.parse import urljoin

from .external_evidence_scan import SourceBusyError, SourceSearchError
from .ryerson_adapter import parse_ryerson_results
from .ryerson_harvest import cache_harvest_rows, cross_match_cached_notices
from .ryerson_safari_transport import (
    BrowserTransportUnavailable,
    RYERSON_SEARCH_URL,
    _ryerson_page_is_busy,
    _safari_do_javascript,
    _safari_open,
    _safari_snapshot,
)


@dataclass(frozen=True)
class HarvestPage:
    page_number: int
    url: str
    rows: tuple[dict, ...]


def _annual_form_javascript(location: str, year: int) -> str:
    location_json=json.dumps(location or "")
    year_json=json.dumps(str(int(year)))
    return f"""
(() => {{
  const loc=document.querySelector('[name="search_lo"]');
  const y1=document.querySelector('[name="search_y1"]');
  const y2=document.querySelector('[name="search_y2"]');
  const submit=document.querySelector('[name="search"][type="submit"]');
  if (!loc) return JSON.stringify({{status:'form_not_recognised',reason:'location field not found'}});
  if (!y1 || !y2) return JSON.stringify({{status:'form_not_recognised',reason:'year fields not found'}});
  if (!submit) return JSON.stringify({{status:'form_not_recognised',reason:'submit field not found'}});

  loc.value={location_json};
  y1.value={year_json};
  y2.value={year_json};
  for (const el of [loc,y1,y2]) {{
    el.dispatchEvent(new Event('input',{{bubbles:true}}));
    el.dispatchEvent(new Event('change',{{bubbles:true}}));
  }}
  submit.click();
  return JSON.stringify({{status:'submitted'}});
}})()
""".strip()


def _pagination_javascript() -> str:
    # Only return visible anchor destinations that plausibly represent result
    # pagination. We intentionally do not click arbitrary forms/buttons here.
    return r"""
(() => {
  const current=location.href;
  const out=[];
  for (const a of [...document.querySelectorAll('a[href]')]) {
    const text=(a.innerText || a.textContent || '').trim();
    const href=a.href || '';
    const low=(text+' '+href).toLowerCase();
    if (!text || !href) continue;
    if (/^(next|older|more|[0-9]+|[>»]+)$/i.test(text) ||
        low.includes('page=') || low.includes('offset=') || low.includes('start=')) {
      out.push({text,href});
    }
  }
  return JSON.stringify({current,links:out});
})()
"""


def _decode_js_json(raw: str, label: str):
    try:
        return json.loads(raw)
    except Exception as exc:
        raise SourceSearchError(f"Could not decode Safari {label}: {raw[:200]}") from exc


def _wait_for_page(*, timeout_seconds=45.0, poll_seconds=1.0, sleep=time.sleep):
    started=time.monotonic()
    last_url=""
    last_html=""
    while time.monotonic()-started < timeout_seconds:
        sleep(poll_seconds)
        url,html=_safari_snapshot()
        last_url,last_html=url,html
        if _ryerson_page_is_busy(html):
            raise SourceBusyError("Ryerson server overloaded; retry later")
        if html and ("<table" in html.casefold() or "ryerson" in html.casefold()):
            return url,html
    raise SourceSearchError(
        f"Timed out waiting for Ryerson page; last URL={last_url!r}, html={len(last_html)} bytes"
    )


def submit_annual_location_search(
    location: str,
    year: int,
    *,
    timeout_seconds: float = 45.0,
    poll_seconds: float = 1.0,
):
    _safari_open(RYERSON_SEARCH_URL)
    _wait_for_page(timeout_seconds=timeout_seconds,poll_seconds=poll_seconds)

    raw=_safari_do_javascript(_annual_form_javascript(location,year))
    result=_decode_js_json(raw,"annual-search submission")
    if result.get("status")!="submitted":
        raise BrowserTransportUnavailable(
            result.get("reason") or "Ryerson annual search form could not be recognised"
        )

    return _wait_for_page(
        timeout_seconds=timeout_seconds,
        poll_seconds=poll_seconds,
    )


def pagination_links() -> list[dict]:
    raw=_safari_do_javascript(_pagination_javascript())
    data=_decode_js_json(raw,"pagination")
    current=data.get("current","")
    out=[]
    seen=set()

    for item in data.get("links",[]):
        raw_href=item.get("href") or ""
        href=urljoin(current,raw_href)
        text=(item.get("text") or "").strip()
        if not text or not href:
            continue

        # Ryerson's pager can expose several distinct JavaScript controls with
        # the same literal # target. urljoin normalises that fragment away, so
        # preserve the raw control identity before comparing the resolved URL.
        shared_hash=raw_href.rstrip().endswith("#")
        if href==current and not shared_hash:
            continue
        if shared_hash:
            identity=("control",text.casefold())
        else:
            identity=("href",href)

        if identity in seen:
            continue
        seen.add(identity)
        out.append({"text":text,"href":href})

    return out


def _page_number_from_link(text: str, href: str, fallback: int) -> int:
    if text.isdigit():
        return int(text)
    for pattern in (r"[?&]page=(\d+)",r"[?&]p=(\d+)",r"[?&]start=(\d+)"):
        m=re.search(pattern,href,re.I)
        if m:
            n=int(m.group(1))
            return n if "start=" not in pattern else fallback
    return fallback


def harvest_location_year(
    db,
    location: str,
    year: int,
    *,
    max_pages: int = 20,
    timeout_seconds: float = 45.0,
    poll_seconds: float = 1.0,
):
    """Harvest a location/year query, following ordinary anchor pagination."""
    url,html=submit_annual_location_search(
        location,year,timeout_seconds=timeout_seconds,poll_seconds=poll_seconds
    )

    visited=set()
    pages=[]
    inserted=0
    existing=0
    pending=[(1,url,html)]

    while pending and len(pages)<max_pages:
        page_number,url,html=pending.pop(0)
        if url in visited:
            continue
        visited.add(url)

        if _ryerson_page_is_busy(html):
            raise SourceBusyError("Ryerson server overloaded; retry later")

        rows=parse_ryerson_results(html)
        cached=cache_harvest_rows(
            db,
            rows,
            harvest_kind="location",
            harvest_value=location,
            harvest_year=year,
            page_number=page_number,
        )
        inserted+=cached["inserted"]
        existing+=cached["existing"]
        pages.append(HarvestPage(page_number,url,tuple(rows)))

        links=pagination_links()
        for i,item in enumerate(links,2):
            href=item["href"]
            if href in visited or any(x[1]==href for x in pending):
                continue
            pn=_page_number_from_link(item["text"],href,i)
            _safari_open(href)
            next_url,next_html=_wait_for_page(
                timeout_seconds=timeout_seconds,poll_seconds=poll_seconds
            )
            pending.append((pn,next_url,next_html))

    # If exactly max_pages were consumed and more unique links remain, surface it.
    truncated=bool(pending)
    return {
        "location":location,
        "year":int(year),
        "pages":len(pages),
        "rows":sum(len(p.rows) for p in pages),
        "inserted":inserted,
        "existing":existing,
        "truncated":truncated,
        "page_details":pages,
    }


def harvest_and_cross_match(
    db,
    location: str,
    year: int,
    *,
    max_pages: int = 20,
    minimum_score: int = 55,
):
    harvest=harvest_location_year(db,location,year,max_pages=max_pages)
    matches=cross_match_cached_notices(
        db,
        year=year,
        harvest_kind="location",
        harvest_value=location,
        minimum_score=minimum_score,
    )
    return {"harvest":harvest,"matches":matches}
