from __future__ import annotations
from dataclasses import dataclass
from .knowledge_graph import relationship_path

@dataclass
class RelationshipResult:
    start_id: int
    end_id: int
    label: str
    reciprocal: str
    confidence: str
    path: list

def _person(db,pid):
    return db.execute("SELECT id,display_name,sex FROM people WHERE id=?",(pid,)).fetchone()

def _name(db,pid):
    r=_person(db,pid)
    return r["display_name"] if r else f"Person {pid}"

def _sex(db,pid):
    r=_person(db,pid)
    return (r["sex"] or "").upper() if r else ""

def _gendered(sex,male,female,neutral):
    return male if sex=="M" else female if sex=="F" else neutral

def _ordinal(n):
    words={1:"first",2:"second",3:"third",4:"fourth",5:"fifth",6:"sixth",7:"seventh",8:"eighth"}
    return words.get(n,f"{n}th")

def _great_prefix(n):
    # n=1 -> uncle; n=2 -> great-uncle; n=3 -> 2× great-uncle
    if n<=1:return ""
    if n==2:return "great-"
    return f"{n-1}× great-"

def _direct_label(db,start,end,rels,adj=None):
    sx=_sex(db,start)
    ex=_sex(db,end)
    if not rels:
        return "same person","same person"

    if len(rels)==1:
        r=rels[0]
        if r=="parent":
            return _gendered(sx,"father","mother","parent"), _gendered(ex,"son","daughter","child")
        if r=="child":
            return _gendered(sx,"son","daughter","child"), _gendered(ex,"father","mother","parent")
        if r=="sibling":
            return _gendered(sx,"brother","sister","sibling"), _gendered(ex,"brother","sister","sibling")
        if r=="spouse":
            return _gendered(sx,"husband","wife","spouse"), _gendered(ex,"husband","wife","spouse")

    if all(r=="parent" for r in rels):
        n=len(rels)
        if n==2:
            a=_gendered(sx,"grandfather","grandmother","grandparent")
            b=_gendered(ex,"grandson","granddaughter","grandchild")
        else:
            prefix="great-"*(n-2)
            a=prefix+_gendered(sx,"grandfather","grandmother","grandparent")
            b=prefix+_gendered(ex,"grandson","granddaughter","grandchild")
        return a,b

    if all(r=="child" for r in rels):
        n=len(rels)
        if n==2:
            a=_gendered(sx,"grandson","granddaughter","grandchild")
            b=_gendered(ex,"grandfather","grandmother","grandparent")
        else:
            prefix="great-"*(n-2)
            a=prefix+_gendered(sx,"grandson","granddaughter","grandchild")
            b=prefix+_gendered(ex,"grandfather","grandmother","grandparent")
        return a,b

    # Aunt/uncle: start sibling of an ancestor of end.
    if rels[0]=="sibling" and all(r=="parent" for r in rels[1:]):
        n=len(rels)-1
        middle=relationship_path(db,start,end,adj=adj)[0].right if len(rels)>1 else None
        branch=_sex(db,middle)
        side="maternal " if branch=="F" and n==1 else "paternal " if branch=="M" and n==1 else ""
        kin=_gendered(sx,"uncle","aunt","aunt/uncle")
        rev=_gendered(ex,"nephew","niece","niece/nephew")
        return side+_great_prefix(n)+kin, _great_prefix(n)+rev

    # Niece/nephew: start descends from sibling of end.
    if rels[-1]=="sibling" and all(r=="child" for r in rels[:-1]):
        n=len(rels)-1
        kin=_gendered(sx,"nephew","niece","niece/nephew")
        rev=_gendered(ex,"uncle","aunt","aunt/uncle")
        return _great_prefix(n)+kin, _great_prefix(n)+rev

    # Cousins: climb from start to sibling branch, descend to end.
    if "sibling" in rels and rels.count("sibling")==1:
        i=rels.index("sibling")
        before=rels[:i]; after=rels[i+1:]
        if before and after and all(r=="child" for r in before) and all(r=="parent" for r in after):
            up=len(before); down=len(after)
            degree=min(up,down)
            removed=abs(up-down)
            label=f"{_ordinal(degree)} cousin"
            if removed==1:label+=" once removed"
            elif removed==2:label+=" twice removed"
            elif removed>2:label+=f" {removed} times removed"
            return label,label

    return f"relative ({len(rels)} steps)",f"relative ({len(rels)} steps)"

def interpret_relationship(db,start_id,end_id,max_depth=12,adj=None):
    path=relationship_path(db,start_id,end_id,max_depth,adj=adj)
    if path is None:
        return RelationshipResult(start_id,end_id,"no relationship path found","no relationship path found","none",[])
    rels=[e.relation for e in path]
    label,reciprocal=_direct_label(db,start_id,end_id,rels,adj=adj)
    confidence="high" if label not in ("no relationship path found",) and not label.startswith("relative (") else "structural"
    return RelationshipResult(start_id,end_id,label,reciprocal,confidence,path)

def _role_word(db,e):
    leftsex=_sex(db,e.left); rightsex=_sex(db,e.right)
    if e.relation=="sibling":
        return _gendered(leftsex,"brother","sister","sibling")+" of"
    if e.relation=="parent":
        return _gendered(leftsex,"father","mother","parent")+" of"
    if e.relation=="child":
        return _gendered(leftsex,"son","daughter","child")+" of"
    if e.relation=="spouse":
        return _gendered(leftsex,"husband","wife","spouse")+" of"
    return e.relation+" of"

def format_relationship(db,start_id,end_id):
    a=_name(db,start_id);b=_name(db,end_id)
    rr=interpret_relationship(db,start_id,end_id)
    title=f"Relationship Path & Interpretation — {a} → {b}"
    L=[title,"="*len(title),"",rr.label.title(),"",f"Confidence: {rr.confidence.title()}","",
       "Relationship Chain","------------------"]
    if rr.path is None or not rr.path:
        if start_id==end_id:L.append(f"  {a} (same person)")
        else:L.append("  No structural family path found.")
        return "\n".join(L)
    for i,e in enumerate(rr.path):
        if i==0:L.append(f"  {_name(db,e.left)}")
        L.append(f"    ↓ {_role_word(db,e)}")
        L.append(f"  {_name(db,e.right)}")
    L += ["","Explanation","-----------"]
    if len(rr.path)==1:
        e=rr.path[0]
        L.append(f"  {_name(db,e.left)} is {_role_word(db,e).replace(' of','')} of {_name(db,e.right)}.")
    else:
        for e in rr.path:
            L.append(f"  {_name(db,e.left)} is {_role_word(db,e).replace(' of','')} of {_name(db,e.right)}.")
        if not rr.label.startswith("relative ("):
            L.append(f"  Therefore, {a} is {rr.label} of {b}.")
    return "\n".join(L)
