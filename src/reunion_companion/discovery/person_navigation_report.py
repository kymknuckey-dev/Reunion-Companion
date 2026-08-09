def format_navigation_summary(s):
    lines=[
      "Person Index & Navigation Archaeology Engine",
      "===========================================",
      f"Package files scanned        {s.package_files_scanned:,}",
      f"Person-ID byte hits          {len(s.hits):,}",
      f"Person-index candidates      {len(s.index_candidates):,}",
      f"Controlled snapshot deltas   {len(s.deltas):,}",
      f"Change-log file candidates   {len(s.candidate_change_log_files):,}",
      "",
      "Top Person Index candidates",
      "---------------------------",
      "Score   Encoding  Stride  Offset      IDs        File"
    ]
    for c in s.index_candidates[:20]:
        lines.append(f"{c.score:>6.1%}  {c.encoding:<8} {c.stride:>6} {c.start_offset:>10,}  {','.join(map(str,c.matched_ids)):<10} {c.file}")
    lines += ["","Candidate Change Log files","--------------------------"]
    lines += [f"  {x}" for x in s.candidate_change_log_files[:20]] or ["  (none)"]
    lines += ["","Verdict","-------",s.verdict,s.verdict_reason]
    return "\n".join(lines)

def format_index_candidates(s,limit=80):
    lines=["Person Index Candidates","=======================",
           "Score   Encoding  Stride  Offset      IDs        File"]
    for c in s.index_candidates[:limit]:
        lines.append(f"{c.score:>6.1%}  {c.encoding:<8} {c.stride:>6} {c.start_offset:>10,}  {','.join(map(str,c.matched_ids)):<10} {c.file}")
    return "\n".join(lines)

def format_change_candidates(s):
    lines=["Change Log / Navigation File Candidates","======================================"]
    for f in s.candidate_change_log_files:
        lines.append(f"  {f}")
    if not s.candidate_change_log_files: lines.append("  (none)")
    return "\n".join(lines)

def format_delta(s,label):
    d=next((x for x in s.deltas if x.label==label),None)
    if not d:return f"Snapshot delta not found: {label}"
    lines=[f"Navigation Delta — {d.label}","="*(19+len(d.label)),
           f"Changed Person ID {d.changed_person_id if d.changed_person_id is not None else '-'}",
           f"Changed field     {d.changed_field or '-'}",
           f"Changed files     {len(d.changed_files)}","",
           "Changed runs","------------",
           "File | Start | BeforeLen | AfterLen | Nearby Person IDs"]
    for r in d.runs[:200]:
        lines.append(f"{r.file} | {r.start:,} | {r.before_len} | {r.after_len} | {','.join(map(str,r.nearby_person_ids)) or '-'}")
    return "\n".join(lines)

def navigation_markdown(s):
    lines=["# Person Index & Navigation Archaeology — Build 23","","```text",format_navigation_summary(s),"```",
           "","## Index candidates","",
           "| Score | File | Encoding | Stride | Offset | IDs |",
           "|---:|---|---|---:|---:|---|"]
    for c in s.index_candidates[:200]:
        lines.append(f"| {c.score:.1%} | {c.file} | {c.encoding} | {c.stride} | {c.start_offset} | {', '.join(map(str,c.matched_ids))} |")
    lines += ["","## Controlled deltas",""]
    for d in s.deltas:
        lines += [f"### {d.label}","","```text",format_delta(s,d.label),"```",""]
    lines += ["## Candidate Change Log files",""]
    lines += [f"- `{f}`" for f in s.candidate_change_log_files] or ["- none"]
    lines += ["","## Verdict","",f"**{s.verdict}** — {s.verdict_reason}",
              "","## Evidence boundary","",
              "A Person-ID byte hit or ordered sequence is a navigation/index candidate only. "
              "Build 23 does not label a structure as Reunion's Person Index until controlled edits corroborate it."]
    return "\n".join(lines)+"\n"
