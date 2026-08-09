def format_instance_summary(s):
    return "\n".join([
        "Object Instance Reconstruction Engine",
        "=====================================",
        f"Instance candidates          {len(s.instances):,}",
        f"Resolved regions             {s.resolved_regions:,}",
        f"Unresolved regions           {s.unresolved_region_count:,}",
        f"Object families              {s.object_families:,}",
        f"Families with instances      {s.families_with_instances:,}",
        f"Singleton instances          {s.singleton_instances:,}",
        f"Multi-region instances       {s.multi_region_instances:,}",
        "",
        "Build 21 does not force unresolved semantic-family regions into",
        "individual instances without locality/identity evidence.",
    ])

def format_instance_list(s):
    lines=[
        "Object Instance Candidates",
        "==========================",
        "Confidence  Status                       Object Type          Regions  Person/Record",
    ]
    for i in s.instances:
        owner = i.person_id or i.record_id or "-"
        lines.append(
            f"{i.confidence:>9.1%}  {i.status:<27} "
            f"{i.object_type:<20} {len(i.region_ids):>7}  {owner}"
        )
    return "\n".join(lines)

def format_instance_detail(s, iid):
    i=next((x for x in s.instances if x.instance_id==iid),None)
    if not i:return f"Instance not found: {iid}"
    lines=[
        f"Object Instance — {iid}",
        "="*(18+len(iid)),
        f"Object type  {i.object_type}",
        f"Confidence   {i.confidence:.1%}",
        f"Status       {i.status}",
        f"Person ID    {i.person_id or '-'}",
        f"Record ID    {i.record_id or '-'}",
        f"Regions      {len(i.region_ids)}",
        f"Roles        {', '.join(i.roles) or '-'}",
        f"Probe IDs    {', '.join(i.probe_ids) or '-'}",
        "",
        "Region IDs",
        "----------",
        *[f"  {r}" for r in i.region_ids],
        "",
        "Evidence",
        "--------",
        *[f"  - {e}" for e in i.evidence],
    ]
    return "\n".join(lines)

def instance_markdown(s):
    lines=[
        "# Object Instance Reconstruction — Build 21",
        "",
        "```text",
        format_instance_summary(s),
        "```",
        "",
        "## Instance candidates",
        "",
        "| Instance | Object type | Confidence | Status | Regions | Person | Record |",
        "|---|---|---:|---|---:|---|---|",
    ]
    for i in s.instances:
        lines.append(
            f"| {i.instance_id} | {i.object_type} | {i.confidence:.1%} | "
            f"{i.status} | {len(i.region_ids)} | {i.person_id or '-'} | {i.record_id or '-'} |"
        )
    lines += [
        "",
        "## Unresolved regions",
        "",
        f"{s.unresolved_region_count} regions remain unresolved because the accumulated "
        "pipeline does not yet provide sufficient instance-locality evidence.",
        "",
        "## Evidence boundary",
        "",
        "Build 21 reconstructs instance candidates only where identity/locality evidence exists. "
        "It does not prove Reunion object ownership, internal class identity, or write semantics.",
    ]
    return "\n".join(lines)+"\n"
