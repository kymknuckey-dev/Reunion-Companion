def format_object_summary(s):
    return "\n".join(["Object Reconstruction Engine","============================",
      f"Objects reconstructed        {len(s.objects):,}",f"Object relations             {len(s.relations):,}",
      f"Region memberships           {s.total_members:,}",f"Shared region memberships    {s.shared_members:,}",
      f"Unknown region memberships   {s.unknown_members:,}",f"Verified object candidates   {s.verified_objects:,}",
      f"High-confidence objects      {s.high_confidence_objects:,}",f"Object candidates            {s.candidate_objects:,}","",
      "Object types are evidence-backed hypotheses, not claims about Reunion's private implementation."])

def format_object_list(s):
    lines=["Reconstructed Objects","=====================","Confidence  Complete  Status                     Object"]
    for o in s.objects: lines.append(f"{o.confidence:>9.1%}  {o.completeness:>8.1%}  {o.status:<25} {o.object_type}")
    return "\n".join(lines)

def format_object_detail(s,oid):
    o=next((x for x in s.objects if x.object_id==oid),None)
    if not o:return f"Object not found: {oid}"
    lines=[f"Object Reconstruction — {o.object_type}","="*(25+len(o.object_type)),
           f"Object ID    {o.object_id}",f"Confidence   {o.confidence:.1%}",
           f"Completeness {o.completeness:.1%}",f"Status       {o.status}",f"Members      {len(o.members)}","","Members","-------"]
    for m in o.members: lines.append(f"{m.membership_confidence:>6.1%} {m.role:<14} {m.region_id:<13} {m.semantic_label}")
    return "\n".join(lines)

def object_markdown(s):
    lines=["# Object Reconstruction — Build 20","","```text",format_object_summary(s),"```","","## Objects","",
           "| Object | Type | Confidence | Completeness | Status | Members |","|---|---|---:|---:|---|---:|"]
    for o in s.objects: lines.append(f"| {o.object_id} | {o.object_type} | {o.confidence:.1%} | {o.completeness:.1%} | {o.status} | {len(o.members)} |")
    lines+=["","## Relations","","| Relation | Source | Target | Type | Confidence |","|---|---|---|---|---:|"]
    for r in s.relations: lines.append(f"| {r.relation_id} | {r.source_object} | {r.target_object} | {r.relation} | {r.confidence:.1%} |")
    lines+=["","## Evidence boundary","","Build 20 reconstructs logical objects from accumulated semantic evidence. It does not prove internal class names, storage ownership, pointer direction, or write semantics."]
    return "\n".join(lines)+"\n"
