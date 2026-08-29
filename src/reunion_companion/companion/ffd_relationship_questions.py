from __future__ import annotations
from .timeline_engine import timeline_for_person
from .knowledge_conversation import answer_knowledge_question
import re
import html,re
from urllib.parse import quote
from collections import deque
from .identity_discovery import resolve_identity_name, identity_groups_in_text
def esc(v):return html.escape("" if v is None else str(v))
def person(db,pid):
 r=db.execute("SELECT id,display_name,sex FROM people WHERE id=?",(pid,)).fetchone();return dict(r) if r else None
def people(db):return [dict(r) for r in db.execute("SELECT id,display_name,sex FROM people ORDER BY display_name,id")]
def fam_child(db,pid):return [r["family_id"] for r in db.execute("SELECT family_id FROM family_members WHERE person_id=? AND lower(role)='child'",(pid,))]
def fam_spouse(db,pid):return [r["family_id"] for r in db.execute("SELECT family_id FROM family_members WHERE person_id=? AND lower(role) IN ('husband','wife','spouse')",(pid,))]
def parents(db,pid):
 out=[];seen=set()
 for fid in fam_child(db,pid):
  for r in db.execute("""SELECT p.id,p.display_name,p.sex FROM family_members fm JOIN people p ON p.id=fm.person_id
  WHERE fm.family_id=? AND lower(fm.role) IN ('husband','wife','spouse') ORDER BY p.id""",(fid,)):
   if r["id"] not in seen:seen.add(r["id"]);out.append(dict(r))
 return out
def children(db,pid):
 out=[];seen=set()
 for fid in fam_spouse(db,pid):
  for r in db.execute("""SELECT p.id,p.display_name,p.sex FROM family_members fm JOIN people p ON p.id=fm.person_id
  WHERE fm.family_id=? AND lower(fm.role)='child' ORDER BY p.id""",(fid,)):
   if r["id"] not in seen:seen.add(r["id"]);out.append(dict(r))
 return out
def spouses(db,pid):
 out=[];seen=set()
 for fid in fam_spouse(db,pid):
  for r in db.execute("""SELECT p.id,p.display_name,p.sex FROM family_members fm JOIN people p ON p.id=fm.person_id
  WHERE fm.family_id=? AND p.id<>? AND lower(fm.role) IN ('husband','wife','spouse') ORDER BY p.id""",(fid,pid)):
   if r["id"] not in seen:seen.add(r["id"]);out.append(dict(r))
 return out
def sexword(sex,m,f,g):return m if (sex or "").upper()=="M" else f if (sex or "").upper()=="F" else g
def ancestor_label(sex,g):
 if g==1:return sexword(sex,"father","mother","parent")
 if g==2:return sexword(sex,"grandfather","grandmother","grandparent")
 if g==3:return sexword(sex,"great-grandfather","great-grandmother","great-grandparent")
 return sexword(sex,f"{g-2}× great-grandfather",f"{g-2}× great-grandmother",f"{g-2}× great-grandparent")
def descendant_label(sex,g):
 if g==1:return sexword(sex,"son","daughter","child")
 if g==2:return sexword(sex,"grandson","granddaughter","grandchild")
 if g==3:return sexword(sex,"great-grandson","great-granddaughter","great-grandchild")
 return sexword(sex,f"{g-2}× great-grandson",f"{g-2}× great-granddaughter",f"{g-2}× great-grandchild")
def ancestor_distances(db,pid):
 d={pid:0};q=deque([pid])
 while q:
  cur=q.popleft()
  for p in parents(db,cur):
   if p["id"] not in d:d[p["id"]]=d[cur]+1;q.append(p["id"])
 return d
def neighbors(db,pid,blood=True):
 out=[(p,"parent") for p in parents(db,pid)]+[(p,"child") for p in children(db,pid)]
 if not blood:out += [(p,"spouse") for p in spouses(db,pid)]
 return out
def relationship_path(db,a,b,blood_only=True):
 if a==b:return [{"person":person(db,a),"edge":None}]
 q=deque([a]);prev={a:(None,None)}
 while q:
  cur=q.popleft()
  for p,e in neighbors(db,cur,blood_only):
   if p["id"] in prev:continue
   prev[p["id"]]=(cur,e);q.append(p["id"])
 if b not in prev:return []
 seq=[];cur=b
 while cur is not None:
  old,e=prev[cur];seq.append((cur,e));cur=old
 seq.reverse()
 return [{"person":person(db,pid),"edge":None if i==0 else e} for i,(pid,e) in enumerate(seq)]
def suffix(n):
 if 10<=n%100<=20:return "th"
 return {1:"st",2:"nd",3:"rd"}.get(n%10,"th")
def blood_relationship(db,a,b):
 aa=ancestor_distances(db,a)
 if b in aa and b!=a:return {"label":ancestor_label(person(db,b)["sex"],aa[b]),"path":relationship_path(db,a,b)}
 bb=ancestor_distances(db,b)
 if a in bb and b!=a:return {"label":descendant_label(person(db,b)["sex"],bb[a]),"path":relationship_path(db,a,b)}
 common=(set(aa)&set(bb))-{a,b}
 if not common:return None
 ca=min(common,key=lambda x:(aa[x]+bb[x],max(aa[x],bb[x]),x));da,dbb=aa[ca],bb[ca];target=person(db,b)
 if da==dbb==1:label=sexword(target["sex"],"brother","sister","sibling")
 elif da>=2 and dbb==1:
  # b is a sibling of an ancestor of a.  Generalise the kinship name
  # rather than falling through to cousin terminology for deeper generations.
  # da=2 -> uncle/aunt; da=3 -> great-uncle/aunt; da=4 -> great-great-uncle/aunt.
  qualifier=""
  if da==2:
   pth=relationship_path(db,a,ca)
   if len(pth)>=2 and (pth[1].get("edge") or "").casefold()=="parent":
    par=pth[1]["person"]
    qualifier="maternal " if _sex_code(par)=="F" else "paternal " if _sex_code(par)=="M" else ""
  greats="great-"*(da-2)
  label=qualifier+greats+sexword(target["sex"],"uncle","aunt","ancestor's sibling")
 elif da==1 and dbb>=2:
  # b descends from a's sibling: nephew/niece with matching great depth.
  greats="great-"*(dbb-2)
  label=greats+sexword(target["sex"],"nephew","niece","sibling's descendant")
 else:
  degree=min(da,dbb)-1
  if degree<=0:return None
  label=f"{degree}{suffix(degree)} cousin";removed=abs(da-dbb)
  if removed:label+=f", {removed} time{'s' if removed!=1 else ''} removed"
 return {"label":label,"path":relationship_path(db,a,b),"common_ancestor":person(db,ca)}
def _name_tokens(text):
 raw=re.findall(r"[A-Za-zÀ-ÿ'-]+",text or "")
 out=[]
 for x in raw:
  t=x.casefold()
  # Natural possessive question forms: Knuckey's / Knuckey’s -> Knuckey.
  if t.endswith("'s") or t.endswith("’s"):t=t[:-2]
  t=t.strip("'’")
  if t:out.append(t)
 return out

def _person_name_tokens(p):
 return _name_tokens(p.get("display_name",""))

def _match_person_phrase(p,phrase):
 pt=_person_name_tokens(p);qt=_name_tokens(phrase)
 if not qt or not pt:return False
 if qt==pt:return True
 if len(qt)>=2 and qt[0]==pt[0] and qt[-1]==pt[-1]:
  pos=0
  for token in qt:
   try:pos=pt.index(token,pos)+1
   except ValueError:return False
  return True
 return False

def resolve_name(db,phrase):
 phrase=(phrase or "").strip()
 if not phrase:return []
 return resolve_identity_name(db,phrase)

def _exact_phrase_matches(matches,phrase):
 return [p for p in matches if p["display_name"].casefold()==(phrase or "").strip().casefold()]

def named_people(db,q):
 # RC1.0.6: identity discovery understands conservative given-name variants
 # and spouse-surname associations without changing the authoritative Reunion name.
 return identity_groups_in_text(db,q)

def explicit_subject(db,q):
 groups=named_people(db,q)
 if not groups:return {"status":"none","people":[]}
 g=groups[0]
 if len(g["matches"])==1:return {"status":"ok","people":g["matches"],"phrase":g["phrase"]}
 return {"status":"ambiguous","people":g["matches"],"phrase":g["phrase"]}

def explicit_pair(db,q):
 groups=named_people(db,q)
 if len(groups)<2:return {"status":"insufficient","groups":groups}
 a,b=groups[0],groups[1]
 if len(a["matches"])!=1 or len(b["matches"])!=1:
  amb=[]
  if len(a["matches"])!=1:amb.append(a)
  if len(b["matches"])!=1:amb.append(b)
  return {"status":"ambiguous","groups":groups,"ambiguous":amb}
 return {"status":"ok","people":[a["matches"][0],b["matches"][0]],"groups":groups}

def _year_from_event_date(text):
 m=re.search(r"\b(\d{4})\b",text or "")
 return m.group(1) if m else ""

def _identity_years(db,p):
 birth=_first_event(db,p["id"],"birth","born")
 death=_first_event(db,p["id"],"death","died")
 return (_year_from_event_date(_event_date(birth)) if birth else "",
         _year_from_event_date(_event_date(death)) if death else "")

def _identity_label(db,p,include_parent=False):
 by,dy=_identity_years(db,p)
 if by and dy:dates=f"{by}–{dy}"
 elif by:dates=f"born {by}"
 elif dy:dates=f"died {dy}"
 else:dates="dates unknown"
 label=f'{p["display_name"]} ({dates})'
 if include_parent:
  ps=parents(db,p["id"])
  if ps:
   label+=" — child of "+(" and ".join(x["display_name"] for x in ps[:2]))
 return label

def _candidate_question_relevance(db,p,q):
 """Return (has_relevant_data, label) for ambiguity ranking.

 This is deliberately a ranking hint, never an identity filter: candidates without
 the requested fact remain selectable.
 """
 q=(q or "").strip()
 if not q:return False,""
 intent=interpret_question(q)
 domain=_structured_domain(q)
 pid=p["id"]
 if domain:
  found=bool(search_structured_facts(db,pid,q,limit=1).get("results"))
  return found,(domain.replace("_"," ").title()+" recorded" if found else "")
 checks={
  "occupation": lambda: bool(events_of_kind(db,pid,"occupation","occup","job","profession","trade")),
  "birth": lambda: bool(events_of_kind(db,pid,"birth","born")),
  "birth_place": lambda: any(_event_place(r) for r in events_of_kind(db,pid,"birth","born")),
  "death": lambda: bool(events_of_kind(db,pid,"death","died","burial")),
  "death_place": lambda: any(_event_place(r) for r in events_of_kind(db,pid,"death","died")),
  "death_cause": lambda: bool(events_of_kind(db,pid,"death","died")),
  "spouses": lambda: bool(spouses(db,pid)),
  "marriage_fact": lambda: bool(events_of_kind(db,pid,"marriage","married")) or bool(spouses(db,pid)),
  "parents": lambda: bool(parents(db,pid)),
  "father": lambda: any(_sex_code(x)=="M" for x in parents(db,pid)),
  "mother": lambda: any(_sex_code(x)=="F" for x in parents(db,pid)),
  "children": lambda: bool(children(db,pid)),
  "siblings": lambda: bool(siblings(db,pid)),
 }
 fn=checks.get(intent)
 found=bool(fn()) if fn else False
 labels={
  "occupation":"Occupation recorded","birth":"Birth recorded","birth_place":"Birth place recorded",
  "death":"Death recorded","death_place":"Death place recorded","death_cause":"Death recorded",
  "spouses":"Spouse relationship recorded","marriage_fact":"Marriage information recorded",
  "parents":"Parents recorded","father":"Father recorded","mother":"Mother recorded",
  "children":"Children recorded","siblings":"Siblings recorded",
 }
 return found,(labels.get(intent,"") if found else "")

def _identity_group_rank(p):
 kind=p.get("_identity_match_kind","")
 return {
  "recorded-name":0,
  "recorded-given":0,
  "given-variant":1,
  # Both are family/name associations.  Keep them in one presentation group;
  # the detailed sort key decides their relative strength.
  "spouse-surname":2,
  "given-variant-spouse-surname":2,
 }.get(kind,1)

def _identity_display_quality(p):
 """Conservative recognition-quality hint, never an identity fact.

 Penalise obvious placeholder/legacy display forms (numbers, comma-separated
 fragments, one-token names) so a well-described canonical person is not buried
 beneath low-information association records.
 """
 name=(p or {}).get("display_name","") or ""
 score=0
 if any(ch.isdigit() for ch in name):score-=4
 if "," in name:score-=2
 words=[x for x in re.findall(r"[A-Za-zÀ-ÿ'’-]+",name) if x]
 if len(words)>=3:score+=2
 elif len(words)==2:score+=1
 else:score-=2
 return score

def _identity_association_rank(choice):
 kind=choice.get("identity_match_kind") or choice.get("person",{}).get("_identity_match_kind","")
 # A combined given-name-variant + spouse-surname explanation carries two
 # explicit pieces of evidence and should not be buried beneath weak generic
 # association records.  Exact spouse-surname associations remain strong.
 return {"given-variant-spouse-surname":0,"spouse-surname":1}.get(kind,2)

def _identity_recognition(db,p):
 """Short Reunion-grounded context that helps distinguish same-name people."""
 bits=[]
 ss=spouses(db,p["id"])
 if ss:
  bits.append("Spouse: "+", ".join(x["display_name"] for x in ss[:2]))
 ps=parents(db,p["id"])
 if ps:
  bits.append("Parents: "+" and ".join(x["display_name"] for x in ps[:2]))
 return " · ".join(bits)

def _ambiguity_answer(group,db=None,q=""):
 matches=group.get("matches",[])
 if db is None:
  names=", ".join(p["display_name"] for p in matches)
  return {"status":"ambiguous","answer":f'I found more than one person matching “{group.get("phrase","")}”: {names}. Please use a more specific name.',"people":matches}
 labels=[_identity_label(db,p) for p in matches]
 # If labels still collide, add parent context where available.
 if len(set(labels))<len(labels):labels=[_identity_label(db,p,True) for p in matches]
 shown="; ".join(labels)
 choices=[]
 for p,label in zip(matches,labels):
  relevant,relevance_label=_candidate_question_relevance(db,p,q)
  choices.append({"person":p,"label":label,"question_relevant":relevant,"relevance_label":relevance_label,
                  "identity_reason":p.get("_identity_match_reason",""),
                  "identity_match_kind":p.get("_identity_match_kind",""),
                  "identity_group_rank":_identity_group_rank(p),
                  "recognition":_identity_recognition(db,p)})
 return {"status":"ambiguous","kind":"identity-choice",
         "answer":f'I found several people matching “{group.get("phrase","")}”. Which one do you mean? {shown}.',
         "people":matches,"choices":choices,"question":q,"question_domain":_structured_domain(q)}

def _graph_distance(db,start_id,target_id):
 if start_id==target_id:return 0
 seen={start_id};queue=deque([(start_id,0)])
 while queue:
  cur,d=queue.popleft()
  for p,_ in neighbors(db,cur,False):
   nid=p["id"]
   if nid==target_id:return d+1
   if nid not in seen:seen.add(nid);queue.append((nid,d+1))
 return None

def resolve_contextual_group(db,group,subject_id=None,allow_current=True):
 matches=group.get("matches",[]);phrase=group.get("phrase","")
 if not matches:return {"status":"none","matches":[],"phrase":phrase}
 exact=_exact_phrase_matches(matches,phrase)

 # Hard identity rule: if the literal name typed by the user belongs to
 # multiple records, never collapse those records using family proximity.
 # At the no-focus Search entry point, however, preserve credible associated-name
 # candidates as well so many literal duplicates cannot hide the person the user
 # may know through marriage or another explained name association.
 if len(exact)>1:
  kept=matches if subject_id is None else exact
  return {"status":"ambiguous","matches":kept,"phrase":phrase,"reason":"explicit-duplicate-name"}

 if subject_id and allow_current:
  current=person(db,subject_id)
  if current and _match_person_phrase(current,phrase) and any(p["id"]==current["id"] for p in matches):
   return {"status":"ok","person":current,"reason":"current-person"}

 # Preserve the established context rule for partial/shortened names.
 # A single literal match must not defeat a closer contextual partial match
 # (e.g. Victor Knuckey -> Victor Alexander Knuckey from Mervyn's page).
 if subject_id:
  ranked=[(_graph_distance(db,subject_id,p["id"]),p) for p in matches]
  ranked=[(d,p) for d,p in ranked if d is not None]
  if ranked:
   best=min(d for d,_ in ranked);nearest=[p for d,p in ranked if d==best]
   if len(nearest)==1:return {"status":"ok","person":nearest[0],"reason":"nearest-family"}
   return {"status":"ambiguous","matches":nearest,"phrase":phrase,"reason":"distance-tie"}

 if len(exact)==1:return {"status":"ok","person":exact[0],"reason":"literal-exact"}
 if len(matches)==1:return {"status":"ok","person":matches[0],"reason":"unique"}
 return {"status":"ambiguous","matches":matches,"phrase":phrase,"reason":"unresolved"}

def contextual_subject(db,q,subject_id=None):
 groups=named_people(db,q)
 if not groups:return {"status":"none","people":[]}
 r=resolve_contextual_group(db,groups[0],subject_id,True)
 if r["status"]=="ok":return {"status":"ok","people":[r["person"]],"phrase":groups[0]["phrase"],"reason":r["reason"]}
 return {"status":"ambiguous","people":r.get("matches",[]),"phrase":r.get("phrase",""),"reason":r.get("reason")}

def contextual_pair(db,q,subject_id=None):
 groups=named_people(db,q)
 if len(groups)<2:return {"status":"insufficient","groups":groups}
 a=resolve_contextual_group(db,groups[0],subject_id,True)
 if a["status"]!="ok":return {"status":"ambiguous","ambiguous":{"phrase":groups[0]["phrase"],"matches":a.get("matches",[])}}
 b=resolve_contextual_group(db,groups[1],a["person"]["id"],False)
 if b["status"]!="ok":return {"status":"ambiguous","ambiguous":{"phrase":groups[1]["phrase"],"matches":b.get("matches",[])}}
 return {"status":"ok","people":[a["person"],b["person"]],"groups":groups}

def list_answer(name,rel,vals):return f"{name}’s {rel}: "+", ".join(p["display_name"] for p in vals)+"." if vals else f"No {rel} are linked for {name} in the current Reunion data."
def _event_rows(db,pid):
 """Canonical person events: the same representation used by Timeline Intelligence."""
 timeline=timeline_for_person(db,pid)
 return list(timeline["events"]) if timeline else []

def _pick(d,*names):
 for n in names:
  if n in d and d[n] not in (None,""):return str(d[n])
 return ""

def _event_kind(row):
 return _pick(row,"type","event_type","kind","tag","event_name","name").casefold()

def _event_date(row):
 return _pick(row,"date","date_display","display_date","date_text")

def _event_place(row):
 return _pick(row,"place","place_display","place_name","place_text","location")

def _event_value(row):
 return _pick(row,"value","value_text","detail","description","event_value")

def events_of_kind(db,pid,*terms):
 terms=tuple(t.casefold() for t in terms)
 return [r for r in _event_rows(db,pid) if any(t in _event_kind(r) for t in terms)]

def _marriage_fact_rows(db,pid):
 rows=list(events_of_kind(db,pid,"marriage","married"))
 seen={(str(_event_date(r)),str(_event_place(r))) for r in rows}
 for fid in fam_spouse(db,pid):
  f=db.execute("SELECT id,marriage_date,marriage_place FROM families WHERE id=?",(fid,)).fetchone()
  if not f:continue
  d=f["marriage_date"] or "";pl=f["marriage_place"] or ""
  if not d and not pl:continue
  key=(str(d),str(pl))
  if key in seen:continue
  seen.add(key)
  rows.append({"id":f["id"],"event_type":"Marriage","date_text":d,"place_text":pl,"value_text":None,"note_text":None,"gedcom_tag":"FAM-MARR"})
 return rows

def _fact_answer(subject,label,rows):
 if not rows:return {"status":"not-found","answer":f'No {label.lower()} information is linked for {subject["display_name"]} in the current Reunion data.'}
 r=rows[0];date=_event_date(r);place=_event_place(r)
 bits=[]
 if date:bits.append(date)
 if place:bits.append(place)
 detail=" at ".join(bits) if len(bits)==2 else (bits[0] if bits else "recorded")
 return {"status":"ok","kind":"fact","events":rows,"answer":f'{subject["display_name"]} — {label}: {detail}.'}

def interpret_question(q):
 """Map flexible everyday wording onto genealogy intent."""
 low=" ".join(_name_tokens(q))
 def has(*xs):return any(x in low for x in xs)
 if has("related","relationship","relation","connected","connection","line from"):return "relationship"
 if has("like as a child","childhood","growing up"):return "unknown"

 if has("occupation","occupations","job","jobs","work","worked","profession","trade","career"):return "occupation"
 if has("residence","resident","where live","where lived","live","lived","living","address"):return "structured"
 if has("education","school","college","university","study","studied"):return "structured"
 if has("military","army","navy","air force","service","enlisted","war"):return "structured"
 if has("immigration","immigrated","arrival","arrived","emigration","emigrated","migration","migrated"):return "structured"

 if has("how old","age at","current age","age now") or low.strip() in ("age","his age","her age","their age"):return "age"
 # In relational follow-ups the requested fact outranks the relationship noun:
 # "When did his father die?" is a death fact about the father, not a father-list query.
 if has("died","death","die","buried","burial"):
  if has("how did","cause of death","what killed","died from","died of"):return "death_cause"
  if has("where") and has("when","date"):return "death"
  if has("where"):return "death_place"
  return "death"
 if has("born","birth","birthday"):
  if has("where") and has("when","date"):return "birth"
  if has("where"):return "birth_place"
  return "birth"
 if has("grandparent","grandparents","grandfather","grandmother"):return "grandparents"
 if has("sibling","siblings","brother","brothers","sister","sisters"):return "siblings"
 if has("father","dad"):return "father"
 if has("mother","mum","mom"):return "mother"
 if has("parent","parents"):return "parents"
 if has("marry","married","marriage","spouse","wife","husband","partner"):
  if has("when","where","date","place","tell me about"):return "marriage_fact"
  return "spouses"
 if has("child","children","son","daughter","sons","daughters"):return "children"
 if has("event","events","happened","timeline"):return "events"
 if has("place","places","where lived","locations","associated with"):return "places"
 if has("source","sources","evidence","certificate","citation","citations"):return "sources"
 if has("media","photo","photos","photograph","photographs","image","images","document","documents"):return "media"
 if has("oldest ancestor","furthest ancestor","earliest ancestor"):return "oldest_ancestor"
 return "unknown"

def _table_names(db):
 return {r["name"] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}

def _linked_text_items(db,pid,table,keywords):
 if table not in _table_names(db):return []
 cols=[r["name"] for r in db.execute(f"PRAGMA table_info({table})")]
 # Prefer an obvious direct person FK. Avoid speculative joins.
 pcol=next((c for c in ("person_id","owner_person_id") if c in cols),None)
 if not pcol:return []
 rows=[dict(r) for r in db.execute(f"SELECT * FROM {table} WHERE {pcol}=?",(pid,))]
 vals=[]
 for r in rows:
  text=next((str(r[c]) for c in keywords if c in r and r[c] not in (None,"")),None)
  if text and text not in vals:vals.append(text)
 return vals

def _simple_items_answer(subject,label,items):
 if not items:return {"status":"not-found","answer":f'No {label.lower()} are linked directly to {subject["display_name"]} in the current Companion data.'}
 shown=", ".join(items[:12]);more=f" (+{len(items)-12} more)" if len(items)>12 else ""
 return {"status":"ok","kind":"list","answer":f'{subject["display_name"]} — {label}: {shown}{more}.',"items":items}

def _sex_code(p):
 return (p.get("sex") or "").strip().upper() if hasattr(p,"get") else (p["sex"] or "").strip().upper()

def siblings(db,pid):
 result=[];seen=set()
 for par in parents(db,pid):
  for sib in children(db,par["id"]):
   if sib["id"]!=pid and sib["id"] not in seen:
    seen.add(sib["id"]);result.append(sib)
 return result

def _ordinal_index(q):
 low=" ".join(_name_tokens(q))
 raw=(q or "").casefold()
 words={"first":0,"1st":0,"second":1,"2nd":1,"third":2,"3rd":2,"fourth":3,"4th":3,
        "fifth":4,"5th":4,"sixth":5,"6th":5,"seventh":6,"7th":6,"eighth":7,"8th":7,
        "ninth":8,"9th":8,"tenth":9,"10th":9}
 for w,i in words.items():
  if re.search(r"(?<!\w)"+re.escape(w)+r"(?!\w)",raw) or re.search(r"\b"+re.escape(w)+r"\b",low):
   return i
 return None

def _ordinal_label(i):
 n=i+1
 if 10<n%100<14:s="th"
 else:s={1:"st",2:"nd",3:"rd"}.get(n%10,"th")
 return f"{n}{s}"

def _select_ordinal(subject,label,vals,q):
 i=_ordinal_index(q)
 if i is None:return None
 if i>=len(vals):
  return {"status":"not-found","answer":f'{subject["display_name"]} does not have a recorded {_ordinal_label(i)} {label} in the current Reunion data.'}
 p=vals[i]
 return {"status":"ok","kind":"person","people":[p],"answer":f'{subject["display_name"]}’s {_ordinal_label(i)} {label} is {p["display_name"]}.'}

def _friendly_kinship_label(label):
 label=(label or "").strip()
 label=re.sub(r",\s*1 time removed\b", " once removed", label, flags=re.I)
 label=re.sub(r",\s*2 times removed\b", " twice removed", label, flags=re.I)
 label=re.sub(r",\s*(\d+) times removed\b", r" \1 times removed", label, flags=re.I)
 return label

def _human_path_answer(db,a,b,path):
 # relationship_path returns dictionaries: {"person": person, "edge": relation}.
 # Collapse spouse edges at either endpoint into a conversational explanation,
 # while preserving the established direct spouse-of-child wording below.
 if not path or len(path)<2:return None
 start_spouse=(path[1].get("edge") or "").strip().casefold()=="spouse"
 end_spouse=(path[-1].get("edge") or "").strip().casefold()=="spouse"
 # Both named people are connected through their spouses.  Explain the two
 # marriage links first, then state the actual blood relationship between the
 # spouses.  This avoids incorrectly assigning a cousin/uncle/etc. label to
 # either non-blood spouse.
 if start_spouse and end_spouse and len(path)>=5:
  a_partner=path[1]["person"];b_partner=path[-2]["person"]
  rel=blood_relationship(db,a_partner["id"],b_partner["id"])
  if rel:
   a_role=sexword(a_partner.get("sex"),"husband","wife","spouse")
   b_role=sexword(b_partner.get("sex"),"husband","wife","spouse")
   label=_friendly_kinship_label(rel.get("label"))
   return (f'{a["display_name"]} is related to {b["display_name"]} through their spouses. '
           f'{a["display_name"]}’s {a_role} is {a_partner["display_name"]}. '
           f'{b["display_name"]}’s {b_role} is {b_partner["display_name"]}. '
           f'{b_partner["display_name"]} is {a_partner["display_name"]}’s {label}.')
 if end_spouse and len(path)>=4:
  partner=path[-2]["person"]
  rel=blood_relationship(db,a["id"],partner["id"])
  if rel:
   role=sexword(b.get("sex"),"husband","wife","spouse")
   label=_friendly_kinship_label(rel.get("label"))
   return f'{b["display_name"]} is the {role} of {a["display_name"]}’s {label}, {partner["display_name"]}.'
 # Reciprocal form: the path starts with the spouse and then follows the
 # spouse's blood line to the other named person.  Interpret the blood
 # relationship from the other person's point of view so reversing the same
 # question remains conversational instead of falling back to graph prose.
 if start_spouse and len(path)>=4:
  partner=path[1]["person"]
  rel=blood_relationship(db,b["id"],partner["id"])
  if rel:
   role=sexword(partner.get("sex"),"husband","wife","spouse")
   label=_friendly_kinship_label(rel.get("label"))
   return f'{a["display_name"]} is related to {b["display_name"]} through {role} {partner["display_name"]}. {partner["display_name"]} is {b["display_name"]}’s {label}.'
 steps=[]
 for i in range(1,len(path)):
  prev=path[i-1]["person"];cur=path[i]["person"];edge=(path[i].get("edge") or "").strip().casefold()
  if edge=="child":steps.append(f'{cur["display_name"]} is the child of {prev["display_name"]}')
  elif edge=="parent":steps.append(f'{cur["display_name"]} is the parent of {prev["display_name"]}')
  elif edge=="spouse":steps.append(f'{cur["display_name"]} is the spouse of {prev["display_name"]}')
  else:steps.append(f'{cur["display_name"]} is linked to {prev["display_name"]} as {edge or "family"}')
 if len(steps)==1:return steps[0]+"."
 if len(path)==3:
  mid=path[1]["person"];e1=(path[1].get("edge") or "").casefold();e2=(path[2].get("edge") or "").casefold()
  if e1=="child" and e2=="spouse":
   return f'{b["display_name"]} is the spouse of {a["display_name"]}’s child, {mid["display_name"]}.'
 return "; ".join(steps)+"."

def _parse_genealogy_date(text):
 import datetime as _dt
 s=(text or "").strip().upper()
 if not s:return None
 # Exact GEDCOM-like dates only. Approximate/range dates are not used for exact age.
 for fmt in ("%d %b %Y","%d %B %Y","%Y-%m-%d","%d/%m/%Y"):
  try:return _dt.datetime.strptime(s,fmt).date()
  except ValueError:pass
 return None

def _first_event(db,pid,*terms):
 rows=events_of_kind(db,pid,*terms)
 return rows[0] if rows else None

def _age_answer(db,subject):
 import datetime as _dt
 br=_first_event(db,subject["id"],"birth","born")
 if not br:return {"status":"not-found","answer":f'I do not have a recorded birth date for {subject["display_name"]}, so I cannot calculate an age.'}
 bd=_parse_genealogy_date(_event_date(br))
 if not bd:return {"status":"not-found","answer":f'{subject["display_name"]} has a birth date recorded, but it is not precise enough for me to calculate an exact age safely.'}
 dr=_first_event(db,subject["id"],"death","died")
 if dr:
  dd=_parse_genealogy_date(_event_date(dr))
  if dd:
   age=dd.year-bd.year-((dd.month,dd.day)<(bd.month,bd.day))
   return {"status":"ok","kind":"age","answer":f'{subject["display_name"]} was {age} years old when they died.',"age":age}
 today=_dt.date.today()
 age=today.year-bd.year-((today.month,today.day)<(bd.month,bd.day))
 return {"status":"ok","kind":"age","answer":f'{subject["display_name"]} is {age} years old based on the recorded birth date.',"age":age}

def _occupation_answer(db,subject):
 rows=events_of_kind(db,subject["id"],"occupation","occup","job","profession","trade")
 items=[]
 for r in rows:
  value=_event_value(r)
  if value and value!="Y" and value not in items:items.append(value)
 return _simple_items_answer(subject,"Occupations",items)

def _cause_of_death_answer(db,subject):
 rows=events_of_kind(db,subject["id"],"death","died")
 death_date=_event_date(rows[0]) if rows else ""
 cause=""
 for r in rows:
  for key in ("cause","cause_of_death","description","detail","memo","note","text","event_value","value"):
   val=_pick(r,key)
   if val and val != death_date:
    # Only accept text that explicitly presents itself as a cause/circumstance,
    # rather than guessing from arbitrary event notes.
    low=val.casefold()
    if any(x in low for x in ("cause","died of","died from","death due","killed","fatal")):
     cause=val;break
  if cause:break
 if cause:
  return {"status":"ok","kind":"death-cause","answer":f'{subject["display_name"]} — recorded cause/circumstances of death: {cause}.'}
 if death_date:
  return {"status":"not-found","kind":"death-cause","answer":f'{subject["display_name"]} died on {death_date}, but I do not have a recorded cause of death.'}
 return {"status":"not-found","kind":"death-cause","answer":f'I do not have a recorded cause of death for {subject["display_name"]}.'}

def _place_fact_answer(subject,label,rows):
 if not rows:return {"status":"not-found","answer":f'No {label.lower()} information is linked for {subject["display_name"]} in the current Reunion data.'}
 place=_event_place(rows[0])
 if place:return {"status":"ok","kind":"fact","events":rows,"answer":f'{subject["display_name"]} — {label}: {place}.'}
 return {"status":"not-found","answer":f'{subject["display_name"]} has the event recorded, but no {label.lower()} is linked in the current Companion data.'}

STRUCTURED_DOMAIN_ALIASES={
 "residence":("residence","resident","live","lived","living","address","home"),
 "education":("education","school","college","university","study","studied"),
 "military":("military","army","navy","air force","service","enlisted","war"),
 "immigration":("immigration","immigrated","arrival","arrived","emigration","emigrated","migration","migrated"),
 "religion":("religion","baptism","baptised","baptized","christening"),
}
QUESTION_STOPWORDS={"what","when","where","who","how","did","does","do","was","were","is","are","the","a","an","about","tell","me","know","we","of","for","to","in","on","at","with","from","his","her","their","person","family","recorded","records","information","info","anything"}

def _question_terms(q):
 return [t for t in _name_tokens(q) if t not in QUESTION_STOPWORDS]

def _canonical_event_documents(db,pid):
 timeline=timeline_for_person(db,pid)
 if not timeline:return []
 docs=[]
 for e in timeline["events"]:
  pieces=[e.get("type"),e.get("date"),e.get("place"),e.get("value"),e.get("note")]
  docs.append({"kind":"event","id":e.get("id"),"type":e.get("type") or "","date":e.get("date") or "",
               "place":e.get("place") or "","value":e.get("value") or "","note":e.get("note") or "",
               "story":e.get("story") or "","sources":e.get("sources") or [],"media":e.get("media") or [],
               "search_text":" ".join(str(x) for x in pieces if x).casefold()})
 return docs

def _structured_domain(q):
 low=" ".join(_name_tokens(q))
 for domain,aliases in STRUCTURED_DOMAIN_ALIASES.items():
  if any(a in low for a in aliases):return domain
 return None

def _score_structured_doc(doc,q,domain=None):
 score=0;matched=False
 dtype=(doc.get("type") or "").casefold()
 if domain:
  aliases=STRUCTURED_DOMAIN_ALIASES.get(domain,())
  if any(a in dtype for a in aliases):score+=8;matched=True
  elif any(a in doc.get("search_text","") for a in aliases):score+=4;matched=True
 for term in _question_terms(q):
  if term in dtype:score+=4;matched=True
  if term in (doc.get("value") or "").casefold():score+=3;matched=True
  if term in (doc.get("place") or "").casefold():score+=3;matched=True
  if term in (doc.get("note") or "").casefold():score+=2;matched=True
 if not matched:return 0
 if doc.get("date"):score+=1
 if doc.get("place"):score+=1
 if doc.get("value"):score+=1
 return score

def search_structured_facts(db,pid,q,limit=12):
 domain=_structured_domain(q)
 ranked=[(_score_structured_doc(d,q,domain),d) for d in _canonical_event_documents(db,pid)]
 ranked=[x for x in ranked if x[0]>0]
 ranked.sort(key=lambda x:(-x[0],x[1].get("date",""),x[1].get("id") or 0))
 return {"domain":domain,"results":[d for _,d in ranked[:limit]]}

def _render_structured_fact(doc):
 bits=[x for x in (doc.get("date"),doc.get("place"),doc.get("value"),doc.get("note")) if x]
 return f'{doc.get("type") or "Event"}: '+(" — ".join(bits) if bits else "recorded")

def _general_structured_answer(db,subject,q):
 found=search_structured_facts(db,subject["id"],q);rows=found["results"]
 if not rows:return {"status":"not-found","kind":"structured","answer":f'I could not find structured Reunion facts matching that question for {subject["display_name"]}.',"results":[]}
 items=[];seen=set()
 for r in rows:
  text=_render_structured_fact(r)
  if text not in seen:seen.add(text);items.append(text)
 label=found["domain"].replace("_"," ").title() if found["domain"] else "Relevant structured facts"
 answer=f'{subject["display_name"]} — {items[0]}.' if len(items)==1 else f'{subject["display_name"]} — {label}: '+"; ".join(items[:8])+"."
 return {"status":"ok","kind":"structured","answer":answer,"results":rows,"items":items}

def _birth_sort_key(db,p):
 row=_first_event(db,p["id"],"birth","born")
 text=_event_date(row) if row else ""
 parsed=_parse_genealogy_date(text)
 if parsed:return (0,parsed.isoformat(),p["id"])
 m=re.search(r"\b(\d{4})\b",text or "")
 if m:return (1,m.group(1),p["id"])
 return (2,"",p["id"])

def _relative_child_candidates(db,subject,q):
 low=" ".join(_name_tokens(q))
 vals=children(db,subject["id"])
 if "son" in low:vals=[p for p in vals if _sex_code(p)=="M"]
 elif "daughter" in low:vals=[p for p in vals if _sex_code(p)=="F"]
 return vals

def _select_relative_child(db,subject,q):
 low=" ".join(_name_tokens(q))
 if not any(x in low for x in ("child","children","son","sons","daughter","daughters")):return None
 vals=_relative_child_candidates(db,subject,q)
 if not vals:return None
 i=_ordinal_index(q)
 if i is not None:return vals[i] if i<len(vals) else None
 if "oldest" in low or "eldest" in low:
  return sorted(vals,key=lambda p:_birth_sort_key(db,p))[0]
 if "youngest" in low:
  return sorted(vals,key=lambda p:_birth_sort_key(db,p))[-1]
 return None

def _name_fragment_matches(p,fragment):
 """Match a short relationship qualifier such as ``Kym`` against a person name."""
 want=_name_tokens(fragment)
 have=_person_name_tokens(p)
 return bool(want) and all(t in have for t in want)

def _relationship_candidates(db,subject,kin):
 kin=(kin or "").casefold()
 if kin in ("son","sons"):
  return [p for p in children(db,subject["id"]) if _sex_code(p)=="M"]
 if kin in ("daughter","daughters"):
  return [p for p in children(db,subject["id"]) if _sex_code(p)=="F"]
 if kin in ("child","children"):
  return children(db,subject["id"])
 if kin in ("father","dad"):
  return [p for p in parents(db,subject["id"]) if _sex_code(p)=="M"]
 if kin in ("mother","mum","mom"):
  return [p for p in parents(db,subject["id"]) if _sex_code(p)=="F"]
 if kin in ("wife",):
  return [p for p in spouses(db,subject["id"]) if _sex_code(p)=="F"]
 if kin in ("husband",):
  return [p for p in spouses(db,subject["id"]) if _sex_code(p)=="M"]
 if kin in ("spouse","partner"):
  return spouses(db,subject["id"])
 return []

def _resolve_possessive_owner(db,subject,owner_text):
 """Resolve the name immediately before a possessive marker, using longest suffix first."""
 toks=_name_tokens(owner_text)
 if not toks:return {"status":"none"}
 for n in range(min(4,len(toks)),0,-1):
  phrase=" ".join(toks[-n:])
  matches=resolve_name(db,phrase) if n>=2 else [p for p in people(db) if _name_fragment_matches(p,phrase)]
  if not matches:continue
  if subject and any(p["id"]==subject["id"] for p in matches) and _name_fragment_matches(subject,phrase):
   return {"status":"ok","person":subject,"phrase":phrase}
  if subject:
   ranked=[(_graph_distance(db,subject["id"],p["id"]),p) for p in matches]
   ranked=[(d,p) for d,p in ranked if d is not None]
   if ranked:
    best=min(d for d,_ in ranked);nearest=[p for d,p in ranked if d==best]
    if len(nearest)==1:return {"status":"ok","person":nearest[0],"phrase":phrase}
    return {"status":"ambiguous","people":nearest,"phrase":phrase}
  if len(matches)==1:return {"status":"ok","person":matches[0],"phrase":phrase}
  return {"status":"ambiguous","people":matches,"phrase":phrase}
 return {"status":"none"}

def _possessive_relationship_resolution(db,q,subject,selected_identity_id=None):
 """Resolve possessive relationship chains as an intermediate person.

 Supports both explicit named possessives (``Elaine's son [Kym]``) and
 conversational pronoun possessives (``her son [Kym]``, ``his daughter``).
 Once the pronoun is grounded to the current conversational subject, both
 forms intentionally use the same relationship-candidate machinery.
 """
 if not subject:return {"status":"none"}
 raw=(q or "").replace("’","'")
 kin_pat=r"(son|sons|daughter|daughters|child|children|father|dad|mother|mum|mom|wife|husband|spouse|partner)"
 # Build 1.2.4: pronoun possessives are relationship traversals, not aliases
 # for the owner's own terminal relationship query.
 pm=re.search(r"\b(his|her|their)\s+"+kin_pat+r"\b(?:\s+([A-Za-zÀ-ÿ'-]+))?",raw,re.I)
 if pm:
  kin=(pm.group(2) or "").casefold();qual=(pm.group(3) or "").strip()
  if qual.casefold() in {"marry","married","die","died","born","work","worked","have","had","is","was","did","does"}:qual=""
  owner=subject; owner_phrase=subject["display_name"]
 else:
  m=re.search(r"'s\s+"+kin_pat+r"\b(?:\s+([A-Za-zÀ-ÿ'-]+))?",raw,re.I)
  if not m:return {"status":"none"}
  before=raw[:m.start()]
  kin=(m.group(1) or "").casefold();qual=(m.group(2) or "").strip()
  if qual.casefold() in {"marry","married","die","died","born","work","worked","have","had","is","was","did","does"}:qual=""
  owner_r=_resolve_possessive_owner(db,subject,before)
  if owner_r.get("status")=="ambiguous":return {"status":"ambiguous-owner","people":owner_r.get("people",[]),"phrase":owner_r.get("phrase","")}
  if owner_r.get("status")!="ok":return {"status":"none"}
  owner=owner_r["person"]; owner_phrase=owner_r.get("phrase",owner["display_name"])
 vals=_relationship_candidates(db,owner,kin)
 if qual:
  named=[p for p in vals if _name_fragment_matches(p,qual)]
  if named:vals=named
 if selected_identity_id:
  try:
   chosen=next((p for p in vals if p["id"]==int(selected_identity_id)),None)
   if chosen:return {"status":"ok","person":chosen,"owner":owner,"kin":kin,"phrase":f"{owner_phrase}'s {kin}"}
  except Exception:pass
 if len(vals)==1:return {"status":"ok","person":vals[0],"owner":owner,"kin":kin,"phrase":f"{owner_phrase}'s {kin}"}
 if len(vals)>1:return {"status":"ambiguous","people":vals,"owner":owner,"kin":kin,"phrase":f"{owner_phrase}'s {kin}"}
 return {"status":"not-found","people":[],"owner":owner,"kin":kin,"phrase":f"{owner_phrase}'s {kin}"}

def _possessive_is_intermediate(intent,kin):
 terminal={
  "father":{"father","dad"}, "mother":{"mother","mum","mom"},
  "children":{"son","sons","daughter","daughters","child","children"},
  "spouses":{"wife","husband","spouse","partner"},
 }
 return kin not in terminal.get(intent,set())


def _relationship_subject_from_context(db,q,subject,selected_identity_id=None):
 """Resolve a singular relative mentioned inside a larger question.

 This is deliberately a *subject transition*, not a terminal answer.  A query
 such as ``When did his father die?`` resolves the father first and then lets
 the original death intent continue against that resolved person.
 """
 low=" ".join(_name_tokens(q))
 if not subject:return None
 possessive=_possessive_relationship_resolution(db,q,subject,selected_identity_id)
 if possessive.get("status")=="ok":return possessive["person"]
 child=_select_relative_child(db,subject,q)
 if child:return child
 if "father" in low or "dad" in low:
  vals=[p for p in parents(db,subject["id"]) if _sex_code(p)=="M"]
  return vals[0] if len(vals)==1 else None
 if "mother" in low or "mum" in low or "mom" in low:
  vals=[p for p in parents(db,subject["id"]) if _sex_code(p)=="F"]
  return vals[0] if len(vals)==1 else None
 if "wife" in low:
  vals=[p for p in spouses(db,subject["id"]) if _sex_code(p)=="F"]
  return vals[0] if len(vals)==1 else None
 if "husband" in low:
  vals=[p for p in spouses(db,subject["id"]) if _sex_code(p)=="M"]
  return vals[0] if len(vals)==1 else None
 if any(x in low for x in ("spouse","partner")):
  vals=spouses(db,subject["id"]);return vals[0] if len(vals)==1 else None
 return None

def _pronoun_mismatch(subject,q):
 """Return a friendly correction when a simple conversational pronoun conflicts with recorded sex."""
 if not subject:return None
 sex=_sex_code(subject); low=" "+" ".join(_name_tokens(q))+" "
 if sex=="F" and any(f" {x} " in low for x in ("he","him","his")):
  return {"status":"pronoun-mismatch","kind":"correction","answer":f'The current conversation is about {subject["display_name"]}. Did you mean her?'}
 if sex=="M" and any(f" {x} " in low for x in ("she","her","hers")):
  return {"status":"pronoun-mismatch","kind":"correction","answer":f'The current conversation is about {subject["display_name"]}. Did you mean him?'}
 return None

def _answer_question_core(db,q,subject_id=None,selected_identity_id=None,prior_knowledge_intent=None):
 q=(q or "").strip()
 if not q:return {"status":"empty","answer":"Ask a question about this person or family."}
 intent=interpret_question(q)

 # RC1.0.6 QA Pass 4: association-aware explicit names use the same no-focus
 # identity-discovery pipeline at Search and Ask entry points.  Existing
 # conversational proximity remains intact for ordinary canonical/short-name
 # follow-ups (for example, a nearby Victor Knuckey), while spouse-surname/name
 # association candidates must never be pruned merely because Ask already has a
 # conversation focus.
 explicit_groups=named_people(db,q)
 association_kinds={"spouse-surname","given-variant-spouse-surname"}
 has_identity_association=bool(explicit_groups and any(
  p.get("_identity_match_kind") in association_kinds
  for p in explicit_groups[0].get("matches",[])
 ))
 discovery_subject_id=None if subject_id is None or has_identity_association else subject_id

 if intent=="relationship":
  pair=contextual_pair(db,q,discovery_subject_id)
  if pair["status"]=="ambiguous":return _ambiguity_answer(pair["ambiguous"],db,q)
  if pair["status"]=="ok":
   a,b=pair["people"];rel=blood_relationship(db,a["id"],b["id"])
   if rel:
    rel=dict(rel);rel["label"]=_friendly_kinship_label(rel.get("label"))
    return {"status":"ok","kind":"relationship","answer":f'{b["display_name"]} is {a["display_name"]}’s {rel["label"]}.' ,"from":a,"to":b,**rel}
   path=relationship_path(db,a["id"],b["id"],False)
   if path:
    summary=_human_path_answer(db,a,b,path) or f'{a["display_name"]} and {b["display_name"]} are connected through the recorded family structure.'
    return {"status":"ok","kind":"connection","answer":summary,"from":a,"to":b,"path":path}
   return {"status":"not-found","answer":"No recorded family connection was found between those two people."}
  return {"status":"needs-person","answer":"I could not identify both people in that relationship question. Try using both names."}

 explicit=contextual_subject(db,q,discovery_subject_id)
 # A candidate explicitly chosen on the Search ambiguity screen is authoritative
 # for this turn, provided it belongs to the identity candidates extracted from
 # the original question. This preserves the question while switching to the
 # selected canonical Reunion person.
 selected=None
 if selected_identity_id and subject_id is None:
  try:
   candidate_ids={p["id"] for g in named_people(db,q) for p in g.get("matches",[])}
   if int(selected_identity_id) in candidate_ids:selected=person(db,int(selected_identity_id))
  except Exception:selected=None
 if selected:
  subject=selected
 elif explicit["status"]=="ambiguous":
  matches=explicit["people"]
  if selected_identity_id:
   try:selected=next((p for p in matches if p["id"]==int(selected_identity_id)),None)
   except Exception:selected=None
  if selected:
   subject=selected
  else:
   return _ambiguity_answer({"phrase":explicit.get("phrase",""),"matches":matches},db,q)
 else:
  subject=explicit["people"][0] if explicit["status"]=="ok" else (person(db,subject_id) if subject_id else None)
 if not subject:return {"status":"needs-person","answer":"I could not determine which person you mean. Try the person’s name or ask from their Person Story."}

 mismatch=_pronoun_mismatch(subject,q)
 if mismatch:return mismatch

 # FFD 1.7 Build 2: broad story/note questions consume the deterministic
 # Person Knowledge bundle. Ordinary fact and relationship questions remain on
 # the existing structured path below.
 knowledge_answer=answer_knowledge_question(db,subject["id"],q,prior_intent=prior_knowledge_intent)
 if knowledge_answer is not None:
  if knowledge_answer.get("status")!="llm-unavailable":return knowledge_answer
  # If the local narrative engine is offline, preserve deterministic structured
  # answers where the question has an existing structured route.
  if intent not in ("structured","occupation","birth","birth_place","death","death_place","death_cause","marriage_fact","events","places","sources","media"):
   return knowledge_answer

 # Build 1.2.3: a possessive relationship is an intermediate identity, not the
 # terminal relationship answer. Resolve it before applying the outer intent.
 possessive=_possessive_relationship_resolution(db,q,subject,selected_identity_id)
 possessive_intermediate=_possessive_is_intermediate(intent,possessive.get("kin","")) if possessive.get("kin") else False
 if possessive_intermediate and possessive.get("status") in ("ambiguous","ambiguous-owner"):
  return _ambiguity_answer({"phrase":possessive.get("phrase","") or "relative","matches":possessive.get("people",[])},db,q)
 if possessive_intermediate and possessive.get("status")=="not-found":
  return {"status":"not-found","answer":f'No matching {possessive.get("kin","relative")} is linked for {possessive.get("owner",subject)["display_name"]} in the current Reunion data.'}
 if possessive_intermediate and possessive.get("status")=="ok":
  subject=possessive["person"]

 if intent in ("age","occupation","structured","birth","birth_place","death","death_place","death_cause","events","places","sources","media","marriage_fact"):
  if not (possessive_intermediate and possessive.get("status")=="ok"):
   related_subject=_relationship_subject_from_context(db,q,subject,selected_identity_id)
   if related_subject:subject=related_subject

 if intent=="grandparents":
  vals=[];seen=set()
  for p in parents(db,subject["id"]):
   for gp in parents(db,p["id"]):
    if gp["id"] not in seen:seen.add(gp["id"]);vals.append(gp)
  return {"status":"ok","kind":"list","people":vals,"answer":list_answer(subject["display_name"],"grandparents",vals)}
 if intent=="siblings":
  vals=siblings(db,subject["id"])
  low=" ".join(_name_tokens(q))
  if "brother" in low or "brothers" in low:vals=[p for p in vals if _sex_code(p)=="M"];label="brothers"
  elif "sister" in low or "sisters" in low:vals=[p for p in vals if _sex_code(p)=="F"];label="sisters"
  else:label="siblings"
  ord_answer=_select_ordinal(subject,label[:-1] if label.endswith("s") else label,vals,q)
  if ord_answer:return ord_answer
  return {"status":"ok","kind":"list","people":vals,"answer":list_answer(subject["display_name"],label,vals)}
 if intent=="father":
  vals=[p for p in parents(db,subject["id"]) if _sex_code(p)=="M"]
  if not vals:return {"status":"not-found","answer":f'No father is linked for {subject["display_name"]} in the current Reunion data.'}
  return {"status":"ok","kind":"person","people":vals,"answer":f'{subject["display_name"]}’s father: {vals[0]["display_name"]}.'}
 if intent=="mother":
  vals=[p for p in parents(db,subject["id"]) if _sex_code(p)=="F"]
  if not vals:return {"status":"not-found","answer":f'No mother is linked for {subject["display_name"]} in the current Reunion data.'}
  return {"status":"ok","kind":"person","people":vals,"answer":f'{subject["display_name"]}’s mother: {vals[0]["display_name"]}.'}
 if intent=="parents":
  vals=parents(db,subject["id"]);return {"status":"ok","kind":"list","people":vals,"answer":list_answer(subject["display_name"],"parents",vals)}
 if intent=="spouses":
  vals=spouses(db,subject["id"]);return {"status":"ok","kind":"list","people":vals,"answer":list_answer(subject["display_name"],"recorded spouse" if len(vals)==1 else "recorded spouses",vals)}
 if intent=="children":
  low=" ".join(_name_tokens(q))
  vals=children(db,subject["id"])
  if "son" in low or "sons" in low:
   vals=[p for p in vals if _sex_code(p)=="M"];label="son" if len(vals)==1 else "sons";ordinal_label="son"
  elif "daughter" in low or "daughters" in low:
   vals=[p for p in vals if _sex_code(p)=="F"];label="daughter" if len(vals)==1 else "daughters";ordinal_label="daughter"
  else:
   label="children";ordinal_label="child"
  ord_answer=_select_ordinal(subject,ordinal_label,vals,q)
  if ord_answer:return ord_answer
  return {"status":"ok","kind":"list","people":vals,"answer":list_answer(subject["display_name"],label,vals)}
 if intent=="age":return _age_answer(db,subject)
 if intent=="occupation":return _occupation_answer(db,subject)
 if intent=="structured":return _general_structured_answer(db,subject,q)
 if intent=="birth_place":return _place_fact_answer(subject,"Birth place",events_of_kind(db,subject["id"],"birth","born"))
 if intent=="death_place":return _place_fact_answer(subject,"Death place",events_of_kind(db,subject["id"],"death","died"))
 if intent=="death_cause":return _cause_of_death_answer(db,subject)
 if intent=="birth":return _fact_answer(subject,"Birth",events_of_kind(db,subject["id"],"birth","born"))
 if intent=="death":return _fact_answer(subject,"Death",events_of_kind(db,subject["id"],"death","died","burial"))
 if intent=="marriage_fact":return _fact_answer(subject,"Marriage",_marriage_fact_rows(db,subject["id"]))
 if intent=="events":
  rows=_event_rows(db,subject["id"])
  items=[]
  for r in rows:
   bits=[x for x in (_pick(r,"type","event_type","kind","event_name","name"),_event_date(r),_event_place(r)) if x]
   if bits:items.append(" — ".join(bits))
  return _simple_items_answer(subject,"Recorded events",items)
 if intent=="places":
  items=[]
  for r in _event_rows(db,subject["id"]):
   p=_event_place(r)
   if p and p not in items:items.append(p)
  return _simple_items_answer(subject,"Places",items)
 if intent=="sources":
  items=[]
  for table in ("sources","citations"):
   items += [x for x in _linked_text_items(db,subject["id"],table,("title","name","display_name","citation","text")) if x not in items]
  return _simple_items_answer(subject,"Sources",items)
 if intent=="media":
  items=[]
  for table in ("media","media_items"):
   items += [x for x in _linked_text_items(db,subject["id"],table,("title","name","filename","file_name","path","url")) if x not in items]
  return _simple_items_answer(subject,"Media",items)
 if intent=="oldest_ancestor":
  d=ancestor_distances(db,subject["id"]);d.pop(subject["id"],None)
  if not d:return {"status":"not-found","answer":f'No ancestors are linked for {subject["display_name"]}.'}
  g=max(d.values());vals=[person(db,pid) for pid,x in d.items() if x==g]
  return {"status":"ok","kind":"list","people":vals,"answer":f'The furthest linked generation currently found for {subject["display_name"]} is {g} generations back.'}
 structured=_general_structured_answer(db,subject,q)
 if structured["status"]=="ok":return structured
 return {"status":"unsupported","answer":"I could not find a supported structured Reunion fact that answers that question yet. Rich Story, Biography and note interpretation comes in a later build."}

def _suggested_focus_from_answer(db,q,subject_id,selected_identity_id,result):
 """Person the user may choose to move the conversation to after this answer."""
 if result.get("status") in ("ambiguous","needs-person","empty","pronoun-mismatch"):
  return None
 if selected_identity_id:
  try:
   chosen=person(db,int(selected_identity_id))
   if chosen:return chosen
  except Exception:pass
 base=person(db,subject_id) if subject_id else None
 explicit=contextual_subject(db,q,subject_id)
 if explicit.get("status")=="ok" and explicit.get("people"):
  named=explicit["people"][0]
  if not base or named["id"]!=base["id"]:return named
 intent=interpret_question(q)
 if base and intent in ("age","occupation","structured","birth","birth_place","death","death_place","death_cause","events","places","sources","media","marriage_fact"):
  rel=_relationship_subject_from_context(db,q,base,selected_identity_id)
  if rel and rel["id"]!=base["id"]:return rel
 if result.get("kind") in ("person","list") and len(result.get("people",[]))==1:
  p=result["people"][0]
  if not base or p["id"]!=base["id"]:return p
 return None

def _focus_from_answer(db,q,subject_id,selected_identity_id,result):
 """Conversation focus changes only through an explicit user navigation action.

 The person passed as subject_id is therefore sticky.  When a question resolves a
 relative, answer_question exposes that person as question_subject so the UI can
 offer a deliberate 'Move conversation to …' action.
 """
 if subject_id:
  return person(db,subject_id)
 # First question / identity selection establishes the initial focus.
 if selected_identity_id:
  try:
   chosen=person(db,int(selected_identity_id))
   if chosen:return chosen
  except Exception:pass
 ex=contextual_subject(db,q,None)
 if ex.get("status")=="ok" and ex.get("people"):return ex["people"][0]
 if result.get("kind") in ("person","list") and len(result.get("people",[]))==1:return result["people"][0]
 return None

def answer_question(db,q,subject_id=None,selected_identity_id=None,prior_knowledge_intent=None,global_identity_discovery=False):
 # Global Search must not let a literal two-token record suppress other
 # credible identities. Direct name Search already exposes those candidates;
 # natural-language Search now uses the same discovery contract.
 if global_identity_discovery and subject_id is None and not selected_identity_id:
  groups=named_people(db,q)
  if groups:
   g=groups[0]; matches=g.get("matches",[])
   if len(matches)>1 and len(_name_tokens(g.get("phrase","")))<=2:
    return _ambiguity_answer({"phrase":g.get("phrase",""),"matches":matches},db,q)
 r=_answer_question_core(db,q,subject_id,selected_identity_id,prior_knowledge_intent)
 # Preserve an explainable discovery reason for entry-point search.  This is
 # provenance for why Companion considered a person a match, never a claim that
 # Reunion stores the inferred name.
 try:
  matched=None
  if selected_identity_id:
   groups=named_people(db,q)
   for g in groups:
    hit=next((p for p in g.get("matches",[]) if p.get("id")==int(selected_identity_id)),None)
    if hit:
     matched=hit;break
  if matched is None:
   ex=contextual_subject(db,q,subject_id)
   if ex.get("status")=="ok" and ex.get("people"):
    matched=ex["people"][0]
  if matched:
   reason=matched.get("_identity_match_reason","")
   if reason and reason not in ("Exact recorded name","Recorded name","Recorded given name"):
    r["identity_match_reason"]=reason
 except Exception:
  pass
 suggested=_suggested_focus_from_answer(db,q,subject_id,selected_identity_id,r)
 focus=_focus_from_answer(db,q,subject_id,selected_identity_id,r)
 if focus:
  r["context_person"]=focus
  r["context_person_id"]=focus["id"]
 if suggested and (not focus or suggested["id"]!=focus["id"]):
  r["question_subject"]=suggested
  r["question_subject_id"]=suggested["id"]
 return r

def path_html(path):
 parts=[]
 for i,x in enumerate(path):
  if i:parts.append(f"<div class='rq-path-edge'>↓ {esc(x['edge'] or 'family')}</div>")
  p=x["person"];parts.append(f"<a class='rq-path-person' href='/person/{p['id']}'>{esc(p['display_name'])}</a>")
 return "<div class='rq-path'>"+"".join(parts)+"</div>"
def _identity_choice_sort_key(choice):
 label=choice.get("label","")
 m=re.search(r"\b(\d{4})\b",label)
 # Identity strength remains primary.  Requested-fact availability helps order
 # candidates within the same identity class but never turns a weak association
 # into a stronger identity than an exact recorded-name match.
 group=choice.get("identity_group_rank",_identity_group_rank(choice.get("person",{})))
 assoc_rank=_identity_association_rank(choice) if group>=2 else 0
 return (group,
         0 if choice.get("question_relevant") else 1,
         assoc_rank,
         -_identity_display_quality(choice.get("person",{})),
         -choice.get("person",{}).get("_identity_score",0),
         int(m.group(1)) if m else 9999,label.casefold(),choice.get("person",{}).get("id",0))

def _choice_cards(choices,question,subject_id=None,origin_id=None):
 cards=[]
 for c in choices:
  p=c["person"];label=c["label"]
  prefix=p["display_name"]
  meta=label[len(prefix):].strip()
  bits=[f"person={esc(subject_id or '')}",f"selected={p['id']}",f"q={quote(question)}"]
  if origin_id:bits.append(f"origin={origin_id}")
  href="/questions?"+"&".join(bits)
  badge=f"<div class='rq-relevance'>{esc(c.get('relevance_label',''))}</div>" if c.get("question_relevant") and c.get("relevance_label") else ""
  identity_reason=f"<div class='rq-identity-reason'>{esc(c.get('identity_reason',''))}</div>" if c.get("identity_reason") and c.get("identity_reason") not in ("Exact recorded name","Recorded name") else ""
  recognition=f"<div class='rq-identity-meta'>{esc(c.get('recognition',''))}</div>" if c.get("recognition") else ""
  cards.append(f"""<a class='rq-identity-card' href='{href}'>
   <div class='rq-identity-name'>{esc(prefix)}</div>
   <div class='rq-identity-meta'>{esc(meta)}</div>{recognition}{identity_reason}{badge}
   <div class='rq-identity-select'>Answer using this person →</div>
  </a>""")
 return "".join(cards)

def identity_choices_html(r,question,subject_id=None,origin_id=None):
 choices=sorted(r.get("choices",[]),key=_identity_choice_sort_key)
 direct=[c for c in choices if c.get("identity_group_rank",_identity_group_rank(c.get("person",{})))<2]
 associated=[c for c in choices if c not in direct]
 best_likely=[c for c in associated
              if (c.get("identity_match_kind") or c.get("person",{}).get("_identity_match_kind",""))
                 in ("spouse-surname","given-variant-spouse-surname")
              and _identity_display_quality(c.get("person",{}))>=1]
 other_associated=[c for c in associated if c not in best_likely]
 chunks=[]
 if best_likely:
  chunks.append("<div class='rq-choice-section'><div class='rq-choice-section-title'>Best likely matches</div><div class='rq-identity-grid'>"+_choice_cards(best_likely[:6],question,subject_id,origin_id)+"</div></div>")
 if direct:
  visible=direct[:6];extra=direct[6:]
  chunks.append("<div class='rq-choice-section'><div class='rq-choice-section-title'>People recorded with this name</div><div class='rq-identity-grid'>"+_choice_cards(visible,question,subject_id,origin_id)+"</div></div>")
  if extra:
   chunks.append(f"<details class='rq-other-matches'><summary>More people recorded with this name ({len(extra)})</summary><div class='rq-identity-grid'>{_choice_cards(extra,question,subject_id,origin_id)}</div></details>")
 if other_associated:
  chunks.append("<div class='rq-choice-section'><div class='rq-choice-section-title'>Other family/name associations</div><div class='rq-identity-grid'>"+_choice_cards(other_associated[:8],question,subject_id,origin_id)+"</div></div>")
  if len(other_associated)>8:
   chunks.append(f"<details class='rq-other-matches'><summary>More family/name association matches ({len(other_associated)-8})</summary><div class='rq-identity-grid'>{_choice_cards(other_associated[8:],question,subject_id,origin_id)}</div></details>")
 relevant=[c for c in choices if c.get("question_relevant")]
 domain=(r.get("question_domain") or interpret_question(question) or "requested information").replace("_"," ")
 relevance=f"<div class='rq-choice-section-title'>Matches with {esc(domain)} information</div>" if relevant else ""
 nonrelevant=[c for c in choices if not c.get("question_relevant")]
 availability_note=(f"<details class='rq-other-matches'><summary>Other matches — requested information not currently recorded ({len(nonrelevant)})</summary></details>" if relevant and nonrelevant else "")
 return f"""<div class='rq-identity-picker'>
  <div class='rq-identity-title'>Possible people</div>
  <div class='rq-identity-count'>{len(choices)} matching Reunion people. Companion found more than one person who could match the name in your question. The recorded Reunion name remains authoritative.</div>
  {relevance}{''.join(chunks)}{availability_note}
 </div>"""

def answer_html(r,question="",subject_id=None,origin_id=None):
 h="<div class='rq-answer'>"
 if r.get("kind")=="identity-choice":
  h+=identity_choices_html(r,question,subject_id,origin_id)
 else:
  text=r.get('answer','')
  if r.get("kind")=="knowledge":
   paras=[x.strip() for x in str(text).split("\n\n") if x.strip()]
   h+="".join(f"<p>{esc(x)}</p>" for x in paras)
  else:
   h+=f"<p>{esc(text)}</p>"
 if r.get("kind") in ("relationship","connection"):h+=path_html(r.get("path",[]))
 if r.get("kind")=="list":h+="<div class='rq-people'>"+"".join(f"<a class='rq-person-chip' href='/person/{p['id']}'>{esc(p['display_name'])}</a>" for p in r.get("people",[]))+"</div>"
 return h+"</div>"

def questions_body(db,subject_id=None,question="",selected_identity_id=None,origin_id=None,prior_knowledge_intent=None):
 subject=person(db,subject_id) if subject_id else None
 r=answer_question(db,question,subject_id,selected_identity_id,prior_knowledge_intent) if question else None
 active=(r or {}).get("context_person") or subject
 active_id=active["id"] if active else subject_id
 origin=person(db,origin_id) if origin_id else None
 # The first resolved/selected person becomes the immutable origin for this conversation.
 if not origin:origin=subject or active
 origin_id=origin["id"] if origin else None
 ctx=""
 if active:
  origin_note=(f"<span class='rq-focus-origin'>Started with {esc(origin['display_name'])}</span>"
               if origin and origin["id"]!=active["id"] else "")
  actions=[]
  candidate=(r or {}).get("question_subject")
  if candidate and candidate["id"]!=active["id"]:
   actions.append(f"<a class='ffd-inline-link rq-move-focus' href='/questions?person={candidate['id']}&origin={origin_id or candidate['id']}'>Move to {esc(candidate['display_name'])} →</a>")
  if origin and active["id"]!=origin["id"]:
   actions.append(f"<a class='ffd-inline-link rq-return-origin' href='/questions?person={origin['id']}&origin={origin['id']}'>← Return to {esc(origin['display_name'])}</a>")
  action_html=f"<span class='rq-focus-actions'>{''.join(actions)}</span>" if actions else ""
  # Preserve earlier regression-contract wording invisibly while the visible
  # focus UI is deliberately compacted in RC1.0.13.
  legacy_started=(f"Conversation started with <strong>{esc(origin['display_name'])}</strong>. " if origin else "")
  legacy_current=f"Conversation is currently about <strong>{esc(active['display_name'])}</strong>. "
  legacy_move=(f"Move conversation to {esc(candidate['display_name'])} → " if candidate and candidate["id"]!=active["id"] else "")
  legacy_return=(f"← Return to {esc(origin['display_name'])} " if origin and active["id"]!=origin["id"] else "")
  legacy_follow="Follow-up questions can use he, she, his, her, father, mother, spouse or child."
  legacy=f"<span class='rq-legacy-contract' aria-hidden='true'>{legacy_started}{legacy_current}{legacy_move}{legacy_return}{legacy_follow}</span>"
  ctx=(f"<div class='rq-context'>{legacy}<div class='rq-focus-bar'><span class='rq-focus-label'>Conversation</span>"
       f"<strong class='rq-focus-name'>{esc(active['display_name'])}</strong>{origin_note}{action_html}</div>"
       "<div class='rq-followup'>Follow-ups can use he, she, his, her, father, mother, spouse or child. Focus changes only when you choose Move to.</div></div>")
 hidden=f"<input type='hidden' name='origin' value='{esc(origin_id or '')}'>" if origin_id else ""
 topic=(r or {}).get("knowledge_intent") or prior_knowledge_intent
 topic_hidden=f"<input type='hidden' name='topic' value='{esc(topic)}'>" if topic else ""
 return f"""<div class='rq-heading'><div class='ffd-eyebrow'>Relationship questions</div><h1>Ask about the family</h1>{ctx}</div>
 <form class='rq-form' method='get' action='/questions'><input type='hidden' name='person' value='{esc(active_id or '')}'>{hidden}{topic_hidden}<input class='rq-input' name='q' value='{esc(question)}' placeholder='Ask a follow-up about this person or family' autofocus><button class='btn' type='submit'>Ask</button></form>
 {answer_html(r,question,active_id,origin_id) if r else ""}
 <div class='card rq-help'><strong>Conversational examples</strong><div class='rq-example'>What religion is James Knuckey?</div><div class='rq-example'>Where was he born?</div><div class='rq-example'>Who were his parents?</div><div class='rq-example'>When did his father die?</div><div class='rq-example'>What about his wife?</div><p>The current person remains the conversational focus until you explicitly move the conversation. Relatives mentioned in an answer can be explored with Move conversation to … . Ambiguous identities still require an explicit selection.</p></div>"""
