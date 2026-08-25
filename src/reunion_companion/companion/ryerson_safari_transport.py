"""Safari-backed Ryerson transport prototype.

Uses the user's real Safari session instead of direct Python HTTP.  This is a
controlled transport layer only; RC1.0.14.6.2 does not attach it to the
persistent unattended runner automatically.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess
import time

from .external_evidence_scan import SourceBusyError, SourceSearchError
from .ryerson_adapter import RyersonQuery, response_is_busy


RYERSON_SEARCH_URL = "https://ryersonindex.org/search.php"

RYERSON_BUSY_PHRASES = (
    "server overloaded",
    "server is feeling a bit overworked",
    "unable to handle the number of requests",
)

def _ryerson_page_is_busy(html: str | None) -> bool:
    low=(html or "").casefold()
    return response_is_busy(200,html) or any(p in low for p in RYERSON_BUSY_PHRASES)


class BrowserTransportUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class SafariProbeResult:
    status: str
    html: str
    url: str


def _run_osascript(script: str, runner=subprocess.run) -> str:
    cp=runner(
        ["osascript","-e",script],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if cp.returncode != 0:
        detail=(cp.stderr or cp.stdout or "").strip()
        low=detail.casefold()
        if (
            "not authorized" in low
            or "not permitted" in low
            or "javascript from apple events" in low
            or "automation" in low
        ):
            raise BrowserTransportUnavailable(detail or "Safari automation is not permitted")
        raise SourceSearchError(detail or f"osascript exited {cp.returncode}")
    return (cp.stdout or "").strip()


def _js_string(value: str) -> str:
    return json.dumps(value or "")


def _form_fill_javascript(query: RyersonQuery) -> str:
    surname=_js_string(query.surname)
    given=_js_string(query.given_names)
    state=_js_string(query.state)

    # The live form contract is intentionally discovered by semantic DOM hints
    # rather than hard-coded field names.
    return f"""
(() => {{
  const norm = s => (s || '').toLowerCase().replace(/[^a-z0-9]+/g,' ');
  const controls = [...document.querySelectorAll('input, select, textarea')];

  function labelText(el) {{
    let text = '';
    if (el.labels) text += ' ' + [...el.labels].map(x => x.innerText || x.textContent || '').join(' ');
    text += ' ' + (el.name || '') + ' ' + (el.id || '') + ' ' + (el.placeholder || '');
    return norm(text);
  }}

  function findControl(words) {{
    return controls.find(el => {{
      const t=labelText(el);
      return words.some(w => t.includes(w));
    }});
  }}

  function setValue(el, value) {{
    if (!el) return false;
    if (el.tagName === 'SELECT') {{
      const want=norm(value);
      let opt=[...el.options].find(o => norm(o.value)===want || norm(o.textContent)===want);
      if (!opt && want==='sa') opt=[...el.options].find(o => norm(o.textContent).includes('south australia'));
      if (!opt) return false;
      el.value=opt.value;
    }} else {{
      el.value=value;
    }}
    el.dispatchEvent(new Event('input', {{bubbles:true}}));
    el.dispatchEvent(new Event('change', {{bubbles:true}}));
    return true;
  }}

  // RC1.0.14.6.2.2: confirmed live Ryerson field names from Safari DOM.
  // Prefer these exact controls; retain semantic discovery as a fallback.
  const surnameEl=document.querySelector('[name="search_sn"]') || findControl(['surname','last name','family name']);
  const givenEl=document.querySelector('[name="search_gn"]') || findControl(['given names','given name','first name','forename']);
  const stateEl=document.querySelector('[name="search_st"]') || findControl(['state']);

  const okSurname=setValue(surnameEl,{surname});
  const okGiven=setValue(givenEl,{given});
  const okState=setValue(stateEl,{state});

  if (!okSurname) return JSON.stringify({{status:'form_not_recognised',reason:'surname field not found'}});
  if ({given} && !okGiven) return JSON.stringify({{status:'form_not_recognised',reason:'given-name field not found'}});
  if (!okState) return JSON.stringify({{status:'form_not_recognised',reason:'state field not found'}});

  const form=(surnameEl && surnameEl.form) || document.querySelector('form');
  if (!form) return JSON.stringify({{status:'form_not_recognised',reason:'search form not found'}});

  const submit=form.querySelector('[name="search"][type="submit"]') ||
    [...form.querySelectorAll('button,input[type=submit]')].find(el =>
      norm(el.innerText || el.value || el.name || '').includes('search')
    );

  if (submit) submit.click();
  else if (form.requestSubmit) form.requestSubmit();
  else form.submit();

  return JSON.stringify({{status:'submitted'}});
}})()
""".strip()


def _safari_do_javascript(js: str, runner=subprocess.run) -> str:
    """Execute JavaScript in Safari without embedding JS in AppleScript source."""
    scripts=[
        'on run argv',
        'tell application "Safari"',
        'if (count of windows) = 0 then make new document',
        'tell front document',
        'set jsSource to item 1 of argv',
        'set jsResult to do JavaScript jsSource',
        'end tell',
        'end tell',
        'return jsResult',
        'end run',
    ]
    args=["osascript"]
    for part in scripts:
        args += ["-e",part]
    args += ["--",js]
    cp=runner(args,capture_output=True,text=True,timeout=30)
    if cp.returncode != 0:
        detail=(cp.stderr or cp.stdout or "").strip()
        low=detail.casefold()
        if (
            "not authorized" in low
            or "not permitted" in low
            or "javascript from apple events" in low
            or "automation" in low
        ):
            raise BrowserTransportUnavailable(detail or "Safari automation is not permitted")
        raise SourceSearchError(detail or f"osascript exited {cp.returncode}")
    return (cp.stdout or "").strip()

def _safari_open(url: str, runner=subprocess.run):
    # Fresh GET navigation avoids Safari POST-resubmission confirmation.
    script=(
        'tell application "Safari"\n'
        'activate\n'
        'if (count of windows) = 0 then\n'
        f'  make new document with properties {{URL:{json.dumps(url)}}}\n'
        'else\n'
        f'  set URL of front document to {json.dumps(url)}\n'
        'end if\n'
        'end tell'
    )
    _run_osascript(script,runner=runner)


def _safari_snapshot(runner=subprocess.run) -> tuple[str,str]:
    js="JSON.stringify({url:location.href,html:document.documentElement.outerHTML})"
    raw=_safari_do_javascript(js,runner=runner)
    try:
        data=json.loads(raw)
    except Exception as exc:
        raise SourceSearchError(f"Could not decode Safari snapshot: {raw[:200]}") from exc
    return data.get("url",""),data.get("html","")


def safari_fetch(
    query: RyersonQuery,
    *,
    runner=subprocess.run,
    sleep=time.sleep,
    timeout_seconds: float=30.0,
    poll_seconds: float=1.0,
) -> tuple[int,str]:
    """Perform one Ryerson search through Safari and return HTTP-like tuple.

    200 means Safari produced a page suitable for the existing parser.
    Busy pages raise SourceBusyError. Transport/configuration problems raise
    BrowserTransportUnavailable or SourceSearchError.
    """
    _safari_open(RYERSON_SEARCH_URL,runner=runner)

    started=time.monotonic()
    html=""
    url=""
    while time.monotonic()-started < timeout_seconds:
        sleep(poll_seconds)
        try:
            url,html=_safari_snapshot(runner=runner)
        except SourceSearchError:
            continue
        if html and ("<form" in html.casefold() or "ryerson" in html.casefold()):
            break
    if not html:
        raise SourceSearchError("Ryerson search page did not become available in Safari")

    if _ryerson_page_is_busy(html):
        raise SourceBusyError("Ryerson server overloaded; retry later")

    raw=_safari_do_javascript(_form_fill_javascript(query),runner=runner)
    try:
        status=json.loads(raw).get("status")
        reason=json.loads(raw).get("reason")
    except Exception:
        status=None
        reason=None
    if status!="submitted":
        raise BrowserTransportUnavailable(reason or "Ryerson search form could not be recognised in Safari")

    before=url
    started=time.monotonic()
    while time.monotonic()-started < timeout_seconds:
        sleep(poll_seconds)
        url,html=_safari_snapshot(runner=runner)
        if _ryerson_page_is_busy(html):
            raise SourceBusyError("Ryerson server overloaded; retry later")
        # A result may render at the same URL, so accept either navigation or a
        # page that no longer contains the obvious search form only.
        low=html.casefold()
        if url!=before or "surname" in low and "given names" in low and "<table" in low:
            return 200,html

    raise SourceSearchError("Timed out waiting for Ryerson search results in Safari")


def safari_transport_available(*, runner=subprocess.run) -> tuple[bool,str]:
    try:
        _safari_do_javascript("document.title",runner=runner)
        return True,"Safari JavaScript automation available"
    except BrowserTransportUnavailable as exc:
        return False,str(exc)
    except SourceSearchError as exc:
        return False,str(exc)
