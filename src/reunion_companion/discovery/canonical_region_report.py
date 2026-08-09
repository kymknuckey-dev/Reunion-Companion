def format_region_summary(c):
    s=c.build15_summary
    lines=["Canonical Region Extraction","===========================",
      f"Probes                            {s.probes}",
      f"Build 15 unknown spans            {s.unknown_spans:,}",
      f"Recurrent unknown -> save noise   {c.recurrent_unknown_noise:,}",
      f"Probe-specific unknown promoted   {c.promoted_unknown_semantic:,}",
      f"Residual unknown                  {c.residual_unknown:,}",
      f"Region candidates                 {len(c.regions):,}",
      f"Strong candidates                 {sum(r.status=='STRONG_CANDIDATE' for r in c.regions):,}",
      f"Cross-probe overlap pairs         {len(c.overlaps):,}","",
      "CANONICAL requires replicated same-field probes."]
    return "\n".join(lines)

def format_region_map(c,limit=80):
    lines=["Canonical Region Candidate Map","==============================",
      "Status            Conf   Spec   Probe                Region        B range             A range"]
    for r in c.regions[:limit]:
        lines.append(f"{r.status:<17} {r.confidence:>5.1%} {r.specificity:>6.1%} {r.probe_id:<20} {r.region_id:<13} {r.before_start:>7,}..{r.before_end:<7,} {r.after_start:>7,}..{r.after_end:<7,}")
    return "\n".join(lines)

def format_region_probe(c,probe_id):
    rs=[r for r in c.regions if r.probe_id==probe_id]
    item=next((x for x in c.results if x.spec.probe_id==probe_id),None)
    if not item:return f"Probe not found: {probe_id}"
    lines=[f"Canonical Regions — {probe_id}","="*(21+len(probe_id)),
      f"Semantic label   {item.spec.semantic_label}",f"Operation        {item.spec.operation}",
      f"Regions          {len(rs)}",""]
    for r in rs:
        lines += [f"{r.region_id} {r.status}",f"  confidence   {r.confidence:.1%}",
          f"  specificity  {r.specificity:.1%}",f"  before       {r.before_start:,}..{r.before_end:,}",
          f"  after        {r.after_start:,}..{r.after_end:,}",
          f"  spans        {','.join(map(str,r.span_indices))}",""]
    return "\n".join(lines)

def format_region_overlaps(c,limit=50):
    lines=["Canonical Region Signature Overlap","==================================",
      "Jaccard  Shared  Left                 Right"]
    for o in c.overlaps[:limit]:
        lines.append(f"{o.jaccard:>7.1%} {o.shared_signatures:>7}  {o.left_probe:<20} {o.right_probe}")
    if not c.overlaps:lines.append("(no shared promoted signatures)")
    return "\n".join(lines)

def canonical_region_markdown(c):
    lines=["# Canonical Region Extraction","","```text",format_region_summary(c),"```","",
      "## Region candidates","",
      "| Region | Probe | Semantic label | Operation | Status | Confidence | Specificity | Before | After | Spans |",
      "|---|---|---|---|---|---:|---:|---|---|---:|"]
    for r in c.regions:
        lines.append(f"| {r.region_id} | {r.probe_id} | {r.semantic_label} | {r.operation} | {r.status} | {r.confidence:.1%} | {r.specificity:.1%} | {r.before_start}..{r.before_end} | {r.after_start}..{r.after_end} | {r.span_count} |")
    lines += ["","## Evidence boundary","","These are canonical-region candidates. Absolute offsets are observations, not semantic identities. CANONICAL requires replicated same-semantic probes."]
    return "\n".join(lines)+"\n"
