from __future__ import annotations

from dataclasses import dataclass

from .family_publication_model import children, family_partners, spouse_families, person
from .timeline_engine import parse_genealogy_date


@dataclass(frozen=True)
class FamilyScopeEntry:
    family_id: int
    owner_id: int
    depth: int
    state: str
    on_primary_path: bool = False
    parent_family_id: int | None = None


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



def _children_by_birth(db,family_id):
    """Return a family's children in genealogical (oldest-first) order.

    Reunion/GEDCOM import identifiers are stable identities, not a meaningful
    sibling order.  Prefer the recorded Birth event and fall back to person id
    only when no usable date exists.
    """
    rows=list(children(db,family_id))
    def key(row):
        birth=db.execute(
            "SELECT date_text FROM events WHERE person_id=? AND lower(event_type)='birth' ORDER BY id LIMIT 1",
            (row['id'],),
        ).fetchone()
        parsed=parse_genealogy_date(birth['date_text'] if birth else '')
        return (parsed.sort_key,row['id'])
    return sorted(rows,key=key)


def scope_candidate_families(db,start_pid,end_pid):
    """Return an expandable descendant-family hierarchy rooted on the book start.

    Each spouse family belongs to the family in which that spouse was recorded
    as a child.  Sibling families are ordered by the child's recorded birth
    date, not by database ids, so the selector reads as a family rather than an
    implementation traversal.  Branches can then be progressively opened to
    arbitrary practical depth without automatically becoming chapters.
    """
    primary,main_line=paternal_family_path(db,start_pid,end_pid,True)
    if not primary and start_pid!=end_pid:return [],{},[]

    roots=[primary[0]] if primary else [f['id'] for f in spouse_families(db,start_pid)]
    out=[];seen=set()

    def walk(fid,owner,depth,parent_fid):
        if fid in seen or depth>64:
            return
        seen.add(fid)
        out.append((fid,owner,depth,parent_fid))
        if depth==64:
            return
        # Establish the complete sibling level first, in birth order.  The UI
        # then nests each child's family beneath the correct parent family.
        child_families=[]
        for child in _children_by_birth(db,fid):
            for sf in spouse_families(db,child['id']):
                if sf['id'] not in seen:
                    child_families.append((sf['id'],child['id']))
        for child_fid,child_pid in child_families:
            walk(child_fid,child_pid,depth+1,fid)

    for fid in roots:
        walk(fid,main_line.get(fid,start_pid),0,None)

    # A pathological/cousin relationship can make a primary-path family enter
    # through another route. Ensure every primary family is still available.
    present={x[0] for x in out}
    for i,fid in enumerate(primary):
        if fid not in present:
            parent=primary[i-1] if i else None
            out.append((fid,main_line.get(fid,end_pid),i,parent))
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


def build_scope(db,start_pid,end_pid,generations=4,selected_family_ids=None,paternal_path_last=False,branch_order_start_family_id=None):
    primary,main_line,candidates=scope_candidate_families(db,start_pid,end_pid)
    if not primary and start_pid!=end_pid:
        raise ValueError('The selected endpoint is not on the recorded paternal line from the starting person.')
    selected=set(primary if selected_family_ids is None else selected_family_ids)
    entries=[]
    for fid,owner,depth,parent_fid in candidates:
        entries.append(FamilyScopeEntry(fid,owner,depth,'book_section' if fid in selected else 'chart_only',fid in primary,parent_fid))
    # Endpoint spouse families can be deeper than the selector generation limit.
    present={e.family_id for e in entries}
    for fid in primary:
        if fid not in present:
            owner=main_line.get(fid,end_pid)
            entries.append(FamilyScopeEntry(fid,owner,generations,'book_section',True,None))
    # Publication order follows family levels, not the construction spine.
    # The paternal path remains useful for finding/default-selecting the book
    # scope, but reader-facing chapters keep all selected sibling families
    # together (in recorded child birth order) before descending into the next
    # generation.  This preserves the early/original family group at the front
    # of the book while still giving later generations a natural birth-order
    # reading sequence.  Missing birth dates retain the selector's stable fallback.
    by_parent={}
    for e in entries:
        by_parent.setdefault(e.parent_family_id,[]).append(e)
    selected_order=[];visited=set()

    branch_start = int(branch_order_start_family_id) if branch_order_start_family_id else None

    def emit_branch_first(parent_entry):
        """Publish each child's selected branch before moving to the next sibling."""
        child_entries=[e for e in by_parent.get(parent_entry.family_id,[])
                       if e.family_id not in visited]
        for child_entry in child_entries:
            visited.add(child_entry.family_id)
            if child_entry.family_id in selected:
                selected_order.append(child_entry.family_id)
            emit_branch_first(child_entry)

    def emit_descendant_levels(parent_entry):
        # A report configuration may nominate one family as the editorial
        # changeover point. Above it, keep historical sibling-family levels
        # together. From it downward, follow each child's branch in birth order.
        if branch_start is not None and parent_entry.family_id == branch_start:
            emit_branch_first(parent_entry)
            return
        child_entries=[e for e in by_parent.get(parent_entry.family_id,[])
                       if e.family_id not in visited]
        # First establish the complete sibling-family level.
        for child_entry in child_entries:
            visited.add(child_entry.family_id)
            if child_entry.family_id in selected:
                selected_order.append(child_entry.family_id)
        # Only after that level is complete do we descend into each branch.
        for child_entry in child_entries:
            emit_descendant_levels(child_entry)

    for root_entry in by_parent.get(None,[]):
        if root_entry.family_id in visited:
            continue
        visited.add(root_entry.family_id)
        if root_entry.family_id in selected:
            selected_order.append(root_entry.family_id)
        emit_descendant_levels(root_entry)
    # Defensive fallback for any disconnected/pathological candidate.
    for e in entries:
        if e.family_id in visited:
            continue
        visited.add(e.family_id)
        if e.family_id in selected:
            selected_order.append(e.family_id)
        emit_descendant_levels(e)
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


def structure_candidate_families(db,start_pid):
    """Return the complete descendant-family hierarchy rooted on start_pid.

    The hierarchy is independent of any paternal endpoint.  Sibling branches
    follow recorded child birth order, and each child's spouse-family branch is
    nested beneath the family in which that child appears.
    """
    roots=[f['id'] for f in spouse_families(db,start_pid)]
    out=[];seen=set()

    def walk(fid,owner,depth,parent_fid):
        if fid in seen or depth>64:
            return
        seen.add(fid)
        out.append((fid,owner,depth,parent_fid))
        for child in _children_by_birth(db,fid):
            for sf in spouse_families(db,child['id']):
                walk(sf['id'],child['id'],depth+1,fid)

    for fid in roots:
        walk(fid,start_pid,0,None)
    return out


def build_structure_scope(db,start_pid,selected_family_ids=None):
    """Build a Family History scope from selection + genealogy structure.

    Membership is explicit; publication order is derived from the descendant
    family tree.  No paternal endpoint or manual branch-order switch is needed.
    """
    candidates=structure_candidate_families(db,start_pid)
    root_ids=[fid for fid,owner,depth,parent in candidates if parent is None]
    selected=set(root_ids if selected_family_ids is None else selected_family_ids)
    entries=[FamilyScopeEntry(fid,owner,depth,
                              'book_section' if fid in selected else 'chart_only',
                              False,parent)
             for fid,owner,depth,parent in candidates]
    selected_order=[]
    context_person_by_family={}
    for e in entries:
        context_person_by_family[e.family_id]=e.owner_id
        if e.family_id in selected:
            selected_order.append(e.family_id)
    return {
        'start_pid':start_pid,
        'end_pid':None,
        'primary_family_ids':root_ids,
        'main_line_by_family':context_person_by_family,
        'selected_family_ids':selected_order,
        'entries':entries,
    }
