from __future__ import annotations

from dataclasses import dataclass

from .family_publication_model import children, family_partners, spouse_families, person


@dataclass(frozen=True)
class FamilyScopeEntry:
    family_id: int
    owner_id: int
    depth: int
    state: str
    on_primary_path: bool = False


def birth_family(db, person_id):
    return db.execute(
        """SELECT f.* FROM families f
           JOIN family_members fm ON fm.family_id=f.id
           WHERE fm.person_id=? AND lower(fm.role)='child'
           ORDER BY f.id LIMIT 1""",
        (person_id,),
    ).fetchone()


def father(db, person_id):
    fam=birth_family(db,person_id)
    if not fam:return None
    return db.execute(
        """SELECT p.* FROM people p JOIN family_members fm ON fm.person_id=p.id
           WHERE fm.family_id=? AND lower(fm.role)='husband' ORDER BY p.id LIMIT 1""",
        (fam['id'],),
    ).fetchone()


def paternal_person_path(db, start_pid, end_pid):
    """Return start..end when end lies on start's paternal-descendant chain.

    Paternal is a *selection default*, not a persisted property.  We walk the
    recorded father relationship upwards from the requested endpoint so there
    is no guess based on surname or sex.
    """
    chain=[];cur=end_pid;seen=set()
    while cur and cur not in seen:
        seen.add(cur);chain.append(cur)
        if cur==start_pid:return list(reversed(chain))
        dad=father(db,cur)
        cur=dad['id'] if dad else None
    return []


def family_for_parent_child(db,parent_id,child_id):
    return db.execute(
        """SELECT f.* FROM families f
           JOIN family_members pm ON pm.family_id=f.id AND pm.person_id=? AND lower(pm.role) IN ('husband','wife','spouse')
           JOIN family_members cm ON cm.family_id=f.id AND cm.person_id=? AND lower(cm.role)='child'
           ORDER BY f.id LIMIT 1""",
        (parent_id,child_id),
    ).fetchone()


def paternal_family_path(db,start_pid,end_pid,include_endpoint_family=True):
    people=paternal_person_path(db,start_pid,end_pid)
    if not people:return [],{}
    fam_ids=[];main_line={}
    for parent_id,child_id in zip(people,people[1:]):
        fam=family_for_parent_child(db,parent_id,child_id)
        if fam and fam['id'] not in fam_ids:
            fam_ids.append(fam['id']);main_line[fam['id']]=parent_id
    if include_endpoint_family:
        for fam in spouse_families(db,end_pid):
            if fam['id'] not in fam_ids:
                fam_ids.append(fam['id']);main_line[fam['id']]=end_pid
    return fam_ids,main_line


def candidate_families(db,start_pid,generations=4):
    """Families available for manual book-scope selection.

    This mirrors legacy descendant discovery only for the selector.  Publishing
    itself never recursively follows these candidates unless their family IDs
    are explicitly selected.
    """
    out=[];seen_fam=set();seen_people=set()
    def walk(pid,depth):
        if depth>generations or pid in seen_people:return
        seen_people.add(pid)
        for fam in spouse_families(db,pid):
            if fam['id'] not in seen_fam:
                seen_fam.add(fam['id']);out.append((fam['id'],pid,depth))
            if depth<generations:
                for child in children(db,fam['id']):walk(child['id'],depth+1)
    walk(start_pid,0)
    return out



def scope_candidate_families(db,start_pid,end_pid):
    """Return the primary path plus one-family sibling choices around it.

    The selector deliberately does not enumerate the complete descendant tree.
    That would recreate the unwieldy behaviour RC1.0.11 is designed to avoid.
    Each primary family exposes its children and, where recorded, those
    children's spouse families as optional additions.
    """
    primary,main_line=paternal_family_path(db,start_pid,end_pid,True)
    if not primary and start_pid!=end_pid:return [],{},[]
    out=[];seen=set()
    for depth,fid in enumerate(primary):
        owner=main_line.get(fid,end_pid)
        if fid not in seen:
            seen.add(fid);out.append((fid,owner,depth))
        for child in children(db,fid):
            for sf in spouse_families(db,child['id']):
                if sf['id'] not in seen:
                    seen.add(sf['id']);out.append((sf['id'],child['id'],depth+1))
    return primary,main_line,out

def endpoint_candidates(db,start_pid,generations=64):
    """People reachable through recorded father links, including the root."""
    result=[];seen=set();q=[(start_pid,0)]
    while q:
        pid,depth=q.pop(0)
        if pid in seen or depth>generations:continue
        seen.add(pid);p=person(db,pid)
        if p:result.append((p,depth))
        # A paternal continuation can only pass through a family where pid is a
        # recorded spouse/parent. Every child in that family has pid as father
        # only when pid occupies the Husband role.
        fams=db.execute(
            """SELECT DISTINCT f.* FROM families f JOIN family_members fm ON fm.family_id=f.id
               WHERE fm.person_id=? AND lower(fm.role)='husband' ORDER BY f.id""",
            (pid,),
        ).fetchall()
        for fam in fams:
            for child in children(db,fam['id']):q.append((child['id'],depth+1))
    return result


def build_scope(db,start_pid,end_pid,generations=4,selected_family_ids=None):
    primary,main_line,candidates=scope_candidate_families(db,start_pid,end_pid)
    if not primary and start_pid!=end_pid:
        raise ValueError('The selected endpoint is not on the recorded paternal line from the starting person.')
    selected=set(primary if selected_family_ids is None else selected_family_ids)
    entries=[]
    for fid,owner,depth in candidates:
        entries.append(FamilyScopeEntry(fid,owner,depth,'book_section' if fid in selected else 'chart_only',fid in primary))
    # Endpoint spouse families can be deeper than the selector generation limit.
    present={e.family_id for e in entries}
    for fid in primary:
        if fid not in present:
            owner=main_line.get(fid,end_pid)
            entries.append(FamilyScopeEntry(fid,owner,generations,'book_section',True))
    order={fid:i for i,fid in enumerate(primary)}
    selected_order=[fid for fid in primary if fid in selected]
    selected_order.extend(e.family_id for e in entries if e.family_id in selected and e.family_id not in order)
    # A manually promoted family also has a focal person: the descendant through
    # whom the selector reached that family.  Use that person only to orient the
    # incoming-spouse context chart; it does not make the family part of the
    # paternal default path.
    context_person_by_family=dict(main_line)
    for e in entries:
        if e.family_id in selected and e.family_id not in context_person_by_family:
            context_person_by_family[e.family_id]=e.owner_id
    return {
        'start_pid':start_pid,'end_pid':end_pid,
        'primary_family_ids':primary,'main_line_by_family':context_person_by_family,
        'selected_family_ids':selected_order,'entries':entries,
    }
