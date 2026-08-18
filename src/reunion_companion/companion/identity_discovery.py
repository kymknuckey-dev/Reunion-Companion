from __future__ import annotations

"""Human-facing identity discovery over authoritative Reunion people.

Reunion's recorded person name remains authoritative.  This module only builds
search associations that help a user find that person using names they may
reasonably know: conservative given-name variants and a spouse's surname.
Association never asserts that a person adopted a spouse's surname.
"""

import re

# Deliberately conservative.  This is a search aid, not a name-normalisation
# claim.  Extend only with well-understood everyday forms and keep the reason
# visible to the user.
_GIVEN_VARIANT_GROUPS = (
    ("susan", "sue", "susie", "suzy"),
    ("mervyn", "merv"),
    ("william", "bill", "billy", "will"),
    ("elizabeth", "liz", "lizzie", "beth", "betty"),
    ("james", "jim", "jimmy"),
    ("robert", "rob", "bob", "bobby"),
    ("richard", "rick", "ricky"),
    ("margaret", "maggie", "meg"),
    ("katherine", "catherine", "kate", "kathy", "cathy"),
)
_VARIANTS = {name: set(group) for group in _GIVEN_VARIANT_GROUPS for name in group}


def _tokens(text):
    out=[]
    for raw in re.findall(r"[A-Za-zÀ-ÿ'’-]+", text or ""):
        t=raw.casefold()
        if t.endswith("'s") or t.endswith("’s"):
            t=t[:-2]
        t=t.strip("'’")
        if t:out.append(t)
    return out


def _columns(db, table):
    try:
        return {r["name"] for r in db.execute(f"PRAGMA table_info({table})")}
    except Exception:
        return set()


def _people_rows(db):
    cols=_columns(db,"people")
    select=["id","display_name"]
    for c in ("sex","gedcom_xref","given_names","surname","raw_name"):
        if c in cols: select.append(c)
    return [dict(r) for r in db.execute(f"SELECT {','.join(select)} FROM people ORDER BY display_name,id")]


def _given_first(p):
    raw=p.get("given_names") or p.get("display_name") or ""
    ts=_tokens(raw)
    return ts[0] if ts else ""


def _surname(p):
    s=(p.get("surname") or "").strip()
    if s:return s.casefold()
    ts=_tokens(p.get("display_name") or "")
    return ts[-1] if len(ts)>=2 else ""


def _given_relation(query_given, recorded_given):
    if not query_given or not recorded_given:return None
    if query_given==recorded_given:return ("exact", recorded_given)
    group=_VARIANTS.get(query_given,set())
    if recorded_given in group:return ("variant", recorded_given)
    return None


def _spouse_people(db,pid):
    if "family_members" not in {r["name"] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}:
        return []
    rows=db.execute("""SELECT DISTINCT p.id,p.display_name""" +
        (",p.given_names,p.surname" if {"given_names","surname"}.issubset(_columns(db,"people")) else "") +
        """ FROM family_members mine
        JOIN family_members other ON other.family_id=mine.family_id AND other.person_id<>mine.person_id
        JOIN people p ON p.id=other.person_id
        WHERE mine.person_id=?
          AND lower(mine.role) IN ('husband','wife','spouse')
          AND lower(other.role) IN ('husband','wife','spouse')
        ORDER BY p.id""",(pid,)).fetchall()
    return [dict(r) for r in rows]


def resolve_identity_name(db, phrase, limit=1000):
    """Resolve a human-entered personal name to ranked Reunion people.

    Returned person dictionaries may include private `_identity_*` explanation
    fields for UI use.  No database content is modified.
    """
    qt=_tokens(phrase)
    if not qt:return []
    qgiven=qt[0]
    qsurname=qt[-1] if len(qt)>=2 else ""
    results=[]
    for p in _people_rows(db):
        pgiven=_given_first(p); psurname=_surname(p)
        display_tokens=_tokens(p.get("display_name") or "")
        literal_full=(len(qt)>=2 and display_tokens==qt)
        display_given=display_tokens[0] if display_tokens else ""
        display_grel=_given_relation(qgiven,display_given)
        grel=_given_relation(qgiven,pgiven)
        # The literal recorded display name is authoritative for discovery even
        # when Reunion's component given-name field contains a formal variant.
        # This matters for records displayed as e.g. "Sue Knuckey" whose
        # component given name may still be Susan.
        if not grel and not literal_full:continue
        score=None; reason=""; kind=""
        # Single-token searches remain permissive and canonical.
        if len(qt)==1:
            if grel[0]=="exact": score=95; kind="recorded-given"; reason="Recorded given name"
            else: score=75; kind="given-variant"; reason=f"Matched {phrase} as a variation of {pgiven.title()}"
        elif qsurname and psurname==qsurname:
            if literal_full:
                score=125; kind="recorded-name"; reason="Exact recorded name"
            elif display_grel and display_grel[0]=="exact":
                # Query given name is visibly recorded on the person, even when
                # extra middle names/initials make it less than a literal full-name match.
                score=114; kind="recorded-name"; reason="Recorded name"
            elif display_grel and display_grel[0]=="variant":
                score=96; kind="given-variant"; reason=f"Matched {qgiven.title()} as a variation of {display_given.title()}"
            elif grel and grel[0]=="exact":
                # Formal component fields may differ from the displayed everyday name.
                # Keep the candidate, but do not let the hidden formal component outrank
                # a person whose displayed name actually matches the query.
                score=94; kind="given-variant"; reason=f"Matched the recorded given-name component {pgiven.title()}"
            else:
                score=92; kind="given-variant"; reason=f"Matched {qgiven.title()} as a variation of {pgiven.title()}"
        elif qsurname:
            spouse_match=None
            for sp in _spouse_people(db,p["id"]):
                if _surname(sp)==qsurname:
                    spouse_match=sp;break
            if spouse_match:
                if grel[0]=="exact":
                    score=86;kind="spouse-surname"
                    reason=f"Matched through marriage/partnership to {spouse_match['display_name']}"
                else:
                    score=76;kind="given-variant-spouse-surname"
                    reason=f"Matched {qgiven.title()} as a variation of {pgiven.title()} and through marriage/partnership to {spouse_match['display_name']}"
        if score is None:continue
        item=dict(p)
        item["_identity_score"]=score
        item["_identity_match_kind"]=kind
        item["_identity_match_reason"]=reason
        results.append(item)
    results.sort(key=lambda p:(-p.get("_identity_score",0),p.get("display_name","").casefold(),p.get("id",0)))
    return results[:limit]


def identity_groups_in_text(db,text):
    """Find non-overlapping personal-name phrases inside natural language."""
    tokens=_tokens(text); candidates=[];seen=set()
    max_len=min(5,len(tokens))
    for length in range(max_len,1,-1):
        for i in range(len(tokens)-length+1):
            phrase=" ".join(tokens[i:i+length])
            matches=resolve_identity_name(db,phrase,1000)
            if not matches:continue
            ids=tuple(p["id"] for p in matches)
            key=(i,length,ids)
            if key in seen:continue
            seen.add(key);candidates.append((i,length,matches,phrase))
    candidates.sort(key=lambda x:(x[0],-x[1],-max((p.get("_identity_score",0) for p in x[2]),default=0),len(x[2])))
    chosen=[];occupied=set()
    for pos,length,matches,phrase in candidates:
        span=set(range(pos,pos+length))
        if span & occupied:continue
        occupied|=span
        chosen.append({"position":pos,"phrase":phrase,"matches":matches})
    chosen.sort(key=lambda x:x["position"])
    return chosen


def is_natural_language_question(text):
    t=(text or "").strip()
    if not t:return False
    if "?" in t:return True
    ts=_tokens(t)
    if not ts:return False
    starters={"who","what","when","where","why","how","did","does","do","was","were","is","are","tell","which"}
    return ts[0] in starters or len(ts)>=4
