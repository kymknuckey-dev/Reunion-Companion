from __future__ import annotations

from .publishing_v7 import esc
from .family_publication_model import family_partners, children, spouse_families, life_dates
from .descendant_chart import direct_ancestor_couples, _couple_html


def _birth_family(db,pid):
    return db.execute("""SELECT f.* FROM families f JOIN family_members fm ON fm.family_id=f.id
        WHERE fm.person_id=? AND lower(fm.role)='child' ORDER BY f.id LIMIT 1""",(pid,)).fetchone()


def spouse_context_model(db,family_id,main_line_pid,max_ancestor_generations=6):
    """Family-of-origin model for the incoming spouse.

    The current chapter marriage stays the connection point, but the surrounding
    genealogy belongs to the incoming spouse's parents and their family.
    """
    h,w=family_partners(db,family_id)
    spouse=next((p for p in (h,w) if p and p['id']!=main_line_pid),None)
    if not spouse:return None
    birth=_birth_family(db,spouse['id'])
    father,mother=family_partners(db,birth['id']) if birth else (None,None)
    return {
        'family_id':family_id,'husband':h,'wife':w,'spouse':spouse,
        'birth_family':birth,'father':father,'mother':mother,
    }


def _person_line(db,p):
    if not p:return ''
    d=life_dates(db,p['id']);dates=[]
    if d['birth']:dates.append('b. '+d['birth'])
    if d['death']:dates.append('d. '+d['death'])
    suffix=(" <span class='person-dates'>— "+esc(" · ".join(dates))+"</span>") if dates else ""
    return "<strong class='person-name'>"+esc(p['display_name'])+"</strong>"+suffix


def _origin_paternal_couples(db,pid,max_generations):
    if not pid:return []
    birth=_birth_family(db,pid)
    rows=[]
    if birth:
        h,w=family_partners(db,birth['id'])
        if h or w: rows.append({'family':birth,'husband':h,'wife':w})
    older=direct_ancestor_couples(db,pid,max_generations)
    # direct_ancestor_couples is oldest-first; keep the whole line oldest-first.
    return older + rows[-1:] if older else rows


def _paternal_line_html(db,label,pid,max_generations):
    P=[f"<div class='origin-line'><h3>{label}</h3><div class='tree'>"]
    rows=_origin_paternal_couples(db,pid,max_generations)
    if rows:
        for row in rows:
            P.append("<div class='tree-row lineage-couple'>"+_couple_html(db,row['husband'],row['wife'])+"</div>")
    else:
        P.append("<p class='small'>No earlier direct line recorded</p>")
    P.append("</div></div>")
    return "".join(P)


def _origin_descendants_html(db,model):
    """Wife's parents' children, their spouses and their children; stop there."""
    birth=model.get('birth_family')
    if not birth:return ''
    P=["<div class='origin-descendants'><h3>Wife&#x27;s Family &amp; Descendants</h3><div class='tree'>"]
    for child in children(db,birth['id']):
        child_families=spouse_families(db,child['id'])
        if not child_families:
            P.append("<div class='tree-row level-0'>"+_person_line(db,child)+"</div>")
            continue
        for fam in child_families:
            h,w=family_partners(db,fam['id'])
            partner=next((x for x in (h,w) if x and x['id']!=child['id']),None)
            couple=_person_line(db,child)
            if partner: couple += " <span class='couple-separator'>&amp;</span> "+_person_line(db,partner)
            P.append("<div class='tree-row level-0'>"+couple+"</div>")
            for grandchild in children(db,fam['id']):
                P.append("<div class='tree-row level-1'>"+_person_line(db,grandchild)+"</div>")
    P.append("</div></div>")
    return "".join(P)


def spouse_context_chart_html(db,family_id,main_line_pid,max_ancestor_generations=6):
    c=spouse_context_model(db,family_id,main_line_pid,max_ancestor_generations)
    if not c:return ''
    h,w=c['husband'],c['wife']
    father,mother=c['father'],c['mother']

    P=["<section class='descendant-chart spouse-context-chart spouse-origin-chart'>",
       "<h2>Spouse Family &amp; Descendants</h2>",
       "<p class='small'>Chart context only — these families are not expanded as book chapters.</p>",
       "<div class='spouse-origin-lines'>",
       _paternal_line_html(db,"Father&#x27;s Paternal Line",father['id'] if father else None,max_ancestor_generations),
       _paternal_line_html(db,"Mother&#x27;s Paternal Line",mother['id'] if mother else None,max_ancestor_generations),
       "</div>",
       "<div class='wife-parents'><h3>Wife&#x27;s Parents</h3>"]
    if father:P.append("<p class='person-line'>"+_person_line(db,father)+"</p>")
    if mother:P.append("<p class='person-line'>"+_person_line(db,mother)+"</p>")
    if not father and not mother:P.append("<p class='small'>Not recorded</p>")
    P.append("</div>")

    P.append("<div class='spouse-central-family'><h3>Family</h3>")
    if h:P.append("<p class='person-line'><strong>Husband:</strong> "+_person_line(db,h)+"</p>")
    if w:P.append("<p class='person-line'><strong>Wife:</strong> "+_person_line(db,w)+"</p>")
    P.append("</div>")
    P.append(_origin_descendants_html(db,c))
    P.append("</section>")
    return "".join(P)
