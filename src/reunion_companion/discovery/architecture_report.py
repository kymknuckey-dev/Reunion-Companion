def format_architecture_summary(snapshot, corpus):
    return "\n".join([
        "Database Architecture Reconstruction",
        "====================================",
        f"Components                 {len(snapshot.components):,}",
        f"Links                      {len(snapshot.links):,}",
        f"Primary candidates         {snapshot.primary_candidates:,}",
        f"Structural candidates      {snapshot.structural_candidates:,}",
        f"Derived/save-state classes {snapshot.derived_save_state:,}",
        f"Unresolved components      {snapshot.unresolved:,}",
        f"Region candidates          {snapshot.region_candidates:,}",
        f"Strong regions             {snapshot.strong_regions:,}",
        f"Residual UNKNOWN spans     {corpus.residual_unknown:,}",
        "",
        "Roles are evidence-based candidates, not claims about Reunion's private source code.",
    ])

def format_architecture_components(snapshot, limit=80):
    lines = [
        "Architecture Components",
        "=======================",
        "Role                  Conf   Component      Probe                Label",
    ]
    for c in snapshot.components[:limit]:
        lines.append(
            f"{c.role:<21} {c.confidence:>5.1%} {c.component_id:<14} "
            f"{(c.probe_id or '-'):20} {c.label}"
        )
    return "\n".join(lines)

def format_architecture_probe(snapshot, probe_id):
    comps = [c for c in snapshot.components if c.probe_id == probe_id]
    if not comps:
        return f"No architecture component for probe: {probe_id}"
    lines = [f"Architecture Evidence — {probe_id}", "=" * (24 + len(probe_id))]
    for c in comps:
        lines += [
            f"{c.component_id} {c.role}",
            f"  label       {c.label}",
            f"  confidence  {c.confidence:.1%}",
            f"  regions     {', '.join(c.region_ids) or '-'}",
            f"  evidence    {'; '.join(c.evidence)}",
            "",
        ]
    return "\n".join(lines)

def architecture_markdown(snapshot, corpus):
    lines = [
        "# Database Architecture Reconstruction — Build 17",
        "", "```text", format_architecture_summary(snapshot, corpus), "```", "",
        "## Components", "",
        "| ID | Role | Label | Probe | Confidence | Regions |",
        "|---|---|---|---|---:|---|",
    ]
    for c in snapshot.components:
        lines.append(
            f"| {c.component_id} | {c.role} | {c.label} | {c.probe_id or '-'} | "
            f"{c.confidence:.1%} | {', '.join(c.region_ids) or '-'} |"
        )
    lines += [
        "", "## Evidence boundary", "",
        "This is an evidence-based architectural reconstruction, not a claim to "
        "Leister Productions' private implementation.",
    ]
    return "\n".join(lines) + "\n"
