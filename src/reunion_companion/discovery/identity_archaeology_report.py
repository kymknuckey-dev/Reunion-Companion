def format_identity_summary(s):
    lines=[
      "Identity Archaeology Engine","============================",
      f"Total regions               {s.total_regions:,}",
      f"Unresolved regions          {s.unresolved_regions:,}",
      f"Regions with any identity   {s.regions_with_any_identity:,}",
      f"Regions with person_id      {s.regions_with_person_id:,}",
      f"Regions with record_id      {s.regions_with_record_id:,}",
      f"Regions with probe_id       {s.regions_with_probe_id:,}",
      "","Candidate Identity Keys","-----------------------",
      "Score   Coverage  Grade                         Key"
    ]
    for k in s.key_evidence:
        lines.append(f"{k.score:>6.1%}  {k.coverage:>7.1%}  {k.grade:<28} {k.key_name}")
    lines += ["","Verdict","-------",s.verdict,s.verdict_reason]
    return "\n".join(lines)

def format_identity_keys(s):
    lines=["Identity Key Evidence","=====================",
           "Score   Cover   Exclus. Collision Groups  Distinct  Key"]
    for k in s.key_evidence:
        lines.append(f"{k.score:>6.1%} {k.coverage:>7.1%} {k.exclusivity:>7.1%} {k.collision_rate:>8.1%} {k.multi_region_groups:>6} {k.distinct_values:>9}  {k.key_name}")
    return "\n".join(lines)

def format_identity_region(s,rid):
    r=next((x for x in s.regions if x.region_id==rid),None)
    if not r:return f"Region not found: {rid}"
    return "\n".join([
      f"Identity Trace — {rid}","="*(17+len(rid)),
      f"Object type    {r.object_type or '-'}",
      f"Semantic label {r.semantic_label or '-'}",
      f"Unresolved     {'yes' if r.unresolved else 'no'}",
      f"Person IDs     {', '.join(r.person_ids) or '-'}",
      f"Record IDs     {', '.join(r.record_ids) or '-'}",
      f"Probe IDs      {', '.join(r.probe_ids) or '-'}",
      f"Before spans   {', '.join(f'{a}:{b}' for a,b in r.before_spans) or '-'}",
      f"After spans    {', '.join(f'{a}:{b}' for a,b in r.after_spans) or '-'}",
      f"Candidate keys {', '.join(r.candidate_keys) or '-'}",
    ])

def identity_markdown(s):
    lines=["# Identity Archaeology — Build 22","","```text",format_identity_summary(s),"```",
           "","## Candidate identity keys","",
           "| Key | Score | Coverage | Exclusivity | Collision rate | Multi-region groups | Grade |",
           "|---|---:|---:|---:|---:|---:|---|"]
    for k in s.key_evidence:
        lines.append(f"| {k.key_name} | {k.score:.1%} | {k.coverage:.1%} | {k.exclusivity:.1%} | {k.collision_rate:.1%} | {k.multi_region_groups} | {k.grade} |")
    lines += ["","## Verdict","",f"**{s.verdict}** — {s.verdict_reason}",
              "","## Evidence boundary","",
              "Build 22 scores only identity/locality evidence already present in the Stage 16–21 pipeline. "
              "It does not infer hidden identifiers that are not represented in those artifacts."]
    return "\n".join(lines)+"\n"
