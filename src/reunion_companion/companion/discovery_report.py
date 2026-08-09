from pathlib import Path
from .discovery import *

def sec(t):
    return "\n" + t + "\n" + "-" * len(t)

def format_tell(db,pid):
    d=person_evidence_summary(db,pid); p=d['person']; L=[p['display_name'],'='*len(p['display_name'])]
    if d['events']:
        L += [sec('Life')]
        for e in d['events']:
            b=[e['event_type']]+[x for x in (e['date_text'],e['place_text'],e['value_text']) if x and x!='Y']
            L.append('  '+' — '.join(b))
    for k,n in [('parents','Parents'),('spouses','Spouses'),('children','Children'),('siblings','Siblings')]:
        if d['connections'][k]:
            L += [sec(n)] + [f"  {x['display_name']} [ID {x['id']}]" for x in d['connections'][k]]
    if d['media']:
        L += [sec('Documents & Media')] + [f"  {'✓' if x['exists_on_disk'] else 'MISSING'} {x['title'] or Path(x['file_path']).name}" for x in d['media'][:30]]
    if d['notes']:
        L += [sec('Notes')]
        for n in d['notes'][:8]:
            label=n['note_type'] or n['gedcom_tag'] or 'Note'
            t=' '.join(n['text'].split())
            L.append(f"  [{label}]")
            L.append('    '+(t[:320]+'…' if len(t)>320 else t))
    return '\n'.join(L)

def format_timeline(db,pid):
    d=person_evidence_summary(db,pid); name=d['person']['display_name']; L=[f"Timeline — {name}",'='*(11+len(name))]
    for e in d['events']:
        L.append('  '+' — '.join([e['date_text'] or '(undated)',e['event_type']]+[x for x in (e['place_text'],e['value_text']) if x and x!='Y']))
    return '\n'.join(L)

def format_connections(db,pid):
    p=db.execute('SELECT display_name FROM people WHERE id=?',(pid,)).fetchone(); c=relationship_connections(db,pid); L=[f"Connections — {p['display_name']}"]
    for k,n in [('parents','Parents'),('spouses','Spouses'),('children','Children'),('siblings','Siblings')]:
        L += [sec(n)] + ([f"  {x['display_name']} [ID {x['id']}]" for x in c[k]] or ['  (none)'])
    return '\n'.join(L)

def format_family(db,pid):
    p=db.execute('SELECT display_name FROM people WHERE id=?',(pid,)).fetchone(); L=[f"Family — {p['display_name']}"]
    for f,m in family_snapshot(db,pid):
        L += ['', f['gedcom_xref'] or f"Family {f['id']}"]
        if f['marriage_date']:
            L.append('  Marriage: '+f['marriage_date']+((' — '+f['marriage_place']) if f['marriage_place'] else ''))
        L += [f"  {x['role']:<8} {x['display_name']}{' ←' if x['id']==pid else ''}" for x in m]
    return '\n'.join(L)

def format_place(db,t):
    L=[f'Place Explorer — {t}']
    for r in place_search(db,t):
        L.append('  '+' — '.join(x for x in (r['display_name'],r['event_type'],r['date_text'],r['place_text']) if x))
    if len(L)==1: L.append('  (no matching place events)')
    return '\n'.join(L)

def format_find(db,t):
    L=[f'Find — {t}']
    for r in cross_search(db,t):
        L += [f"  {r['kind'].upper():<7} {r['title']}", f"          {r['snippet']}"]
    if len(L)==1: L.append('  (no matches)')
    return '\n'.join(L)

def format_gaps(db,pid):
    p=db.execute('SELECT display_name FROM people WHERE id=?',(pid,)).fetchone(); g=research_gaps(db,pid)
    L=[f"Research Gaps — {p['display_name']}"]
    L += [f'  • {a}: {b}' for a,b in g] or ['  No obvious gaps detected.']
    return '\n'.join(L)

def format_research(db,pid):
    d=person_evidence_summary(db,pid); L=[f"Research — {d['person']['display_name']}", sec('Research Gaps')]
    L += [f'  • {a}: {b}' for a,b in d['gaps']] or ['  No obvious gaps detected.']
    if d['notes']:
        L += [sec('Existing Notes')] + ['  '+(' '.join(n['text'].split())[:300]) for n in d['notes'][:10]]
    return '\n'.join(L)

def _fmtwalk(db,pid,title,walk):
    p=db.execute('SELECT display_name FROM people WHERE id=?',(pid,)).fetchone(); L=[f"{title} — {p['display_name']}"]
    L += [f"  {'  '*(g-1)}G{g}: {x['display_name']} [ID {x['id']}]" for g,x in walk] or ['  (none)']
    return '\n'.join(L)

def format_ancestors(db,pid,g=5): return _fmtwalk(db,pid,'Ancestors',ancestors(db,pid,g))
def format_descendants(db,pid,g=5): return _fmtwalk(db,pid,'Descendants',descendants(db,pid,g))

def format_duplicates(db):
    L=['Duplicate Candidates', sec('People')]
    L += [f"  {x['count']} × {x['display_name']} — IDs {x['ids']}" for x in duplicate_people(db)] or ['  (none)']
    L += [sec('Media paths')]
    L += [f"  {x['count']} × {x['file_path']} — IDs {x['ids']}" for x in duplicate_media(db)] or ['  (none)']
    return '\n'.join(L)

def format_explore(db,pid):
    d=person_evidence_summary(db,pid); c=d['connections']; p=d['person']
    return '\n'.join([p['display_name'],'='*len(p['display_name']),'','PERSON',f"├── Parents ({len(c['parents'])})",f"├── Spouses ({len(c['spouses'])})",f"├── Children ({len(c['children'])})",f"├── Siblings ({len(c['siblings'])})",f"├── Events ({len(d['events'])})",f"├── Media ({len(d['media'])})",f"├── Notes ({len(d['notes'])})",f"└── Research gaps ({len(d['gaps'])})"])
