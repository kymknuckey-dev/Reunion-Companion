"""Formatting for Build 18 Semantic Confidence Engine."""


def format_confidence_summary(snapshot) -> str:
    grades = {}
    for r in snapshot.regions:
        grades[r.grade] = grades.get(r.grade, 0) + 1
    lines = [
        "Semantic Confidence Engine",
        "==========================",
        f"Semantic region rows        {snapshot.semantic_regions:,}",
        f"Exclusive regions           {snapshot.exclusive_regions:,}",
        f"Contradictory regions       {snapshot.contradictory_regions:,}",
        f"High confidence >=90%       {snapshot.high_confidence_regions:,}",
        f"Verified candidates         {snapshot.verified_candidate_regions:,}",
        f"Semantic labels             {snapshot.labels:,}",
        "",
        "Grades",
        "------",
    ]
    for grade in ("VERIFIED_CANDIDATE", "HIGH_CONFIDENCE", "SUPPORTED", "TENTATIVE", "LOW"):
        lines.append(f"{grade:<20} {grades.get(grade, 0):,}")
    lines += [
        "",
        "VERIFIED_CANDIDATE is not CANONICAL. Canonical promotion still requires",
        "independent repeated probes of the same semantic field.",
    ]
    return "\n".join(lines)


def format_confidence_probe(snapshot, probe_id: str, limit=50) -> str:
    rows = [r for r in snapshot.regions if r.probe_id == probe_id]
    if not rows:
        return f"No confidence regions for probe: {probe_id}"
    lines = [
        f"Semantic Confidence — {probe_id}",
        "=" * (22 + len(probe_id)),
        f"Regions   {len(rows)}",
        "",
        "Score   Grade                 Region        Label",
    ]
    for r in rows[:limit]:
        lines.append(
            f"{r.score:>6.1%}  {r.grade:<20} {r.region_id:<13} {r.semantic_label}"
        )
    return "\n".join(lines)


def format_confidence_region(snapshot, region_id: str) -> str:
    rows = [r for r in snapshot.regions if r.region_id == region_id]
    if not rows:
        return f"Region not found: {region_id}"
    lines = [f"Region Confidence — {region_id}", "=" * (20 + len(region_id))]
    for r in rows:
        lines += [
            f"Probe          {r.probe_id}",
            f"Semantic label {r.semantic_label}",
            f"Score          {r.score:.1%}",
            f"Grade          {r.grade}",
            f"Specificity    {r.specificity:.1%}",
            f"Exclusive      {'yes' if r.exclusivity else 'no'}",
            f"Contradiction  {r.contradiction_penalty:.1%}",
            f"Decoded        {'yes' if r.decoded_support else 'no'}",
            f"Object Class   {'yes' if r.object_class_support else 'no'}",
            f"Alignment      {'yes' if r.alignment_support else 'no'}",
            "Evidence",
        ]
        lines += [f"  - {e}" for e in r.evidence]
        lines.append("")
    return "\n".join(lines)


def confidence_markdown(snapshot) -> str:
    lines = [
        "# Semantic Confidence — Build 18",
        "",
        "```text",
        format_confidence_summary(snapshot),
        "```",
        "",
        "## Highest-confidence regions",
        "",
        "| Region | Label | Probe | Score | Grade | Specificity | Direct evidence | Contradiction |",
        "|---|---|---|---:|---|---:|---|---:|",
    ]
    for r in snapshot.regions:
        direct = []
        if r.decoded_support:
            direct.append("decoded")
        if r.object_class_support:
            direct.append("object-class")
        if r.alignment_support:
            direct.append("alignment")
        lines.append(
            f"| {r.region_id} | {r.semantic_label} | {r.probe_id} | "
            f"{r.score:.1%} | {r.grade} | {r.specificity:.1%} | "
            f"{', '.join(direct) or '-'} | {r.contradiction_penalty:.1%} |"
        )
    lines += [
        "",
        "## Evidence boundary",
        "",
        "Build 18 scores evidence. It does not promote a semantic label to CANONICAL. "
        "Repeated independent same-field probes remain necessary.",
    ]
    return "\n".join(lines) + "\n"
