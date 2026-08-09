from pathlib import Path
from .queries import get_person
def _m(m):
    return f"- [{'✓' if m['exists_on_disk'] else 'MISSING'}] {m['title'] or Path(m['file_path']).name} — `{m['file_path']}`"
def person_markdown(db,pid):
    d=get_person(db,pid)
    if not d: raise KeyError(pid)
    p=d["person"]; lines=[f"# {p['display_name']}","",f"- Companion ID: {p['id']}",f"- GEDCOM: {p['gedcom_xref'] or '-'}",f"- Sex: {p['sex'] or '-'}",""]
    if d["events"]:
        lines += ["## Timeline",""]
        for e in d["events"]:
            bits=[e["event_type"]]+[x for x in (e["date_text"],e["place_text"],e["value_text"] if e["value_text"]!="Y" else None) if x]
            lines.append("- "+" — ".join(bits))
        lines.append("")
    if d["relationships"]:
        lines += ["## Family",""]
        for r in d["relationships"]:
            f=r["family"]; head=f"Family {f['gedcom_xref'] or f['id']}"
            if f["marriage_date"] or f["marriage_place"]: head += " — "+" — ".join(x for x in (f["marriage_date"],f["marriage_place"]) if x)
            lines.append("### "+head)
            for m in r["members"]: lines.append(f"- {m['role']}: {m['display_name']}{' ←' if m['id']==pid else ''}")
            lines.append("")
    if d["person_media"]: lines += ["## Person Media",""]+[_m(x) for x in d["person_media"]]+[""]
    if d["event_media"]:
        lines += ["## Event Documents",""]
        cur=None
        for x in d["event_media"]:
            if x["attached_to"]!=cur: cur=x["attached_to"]; lines += ["### "+cur,""]
            lines.append(_m(x))
        lines.append("")
    if d["family_media"]: lines += ["## Family / Marriage Media",""]+[_m(x) for x in d["family_media"]]+[""]
    return "\n".join(lines).rstrip()+"\n"
def write_person_markdown(db,pid,output):
    p=Path(output).expanduser();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(person_markdown(db,pid),encoding="utf-8");return p
