def format_manifest_result(r):
    lines=[
        "Automated Probe Manifest Engine",
        "==============================",
        f"Probe folder                 {r.folder}",
        f"Snapshots discovered         {len(r.snapshots)}",
        f"Known persons                {len(r.persons)}",
        "",
        "Snapshots",
        "---------",
        "Seq   Person   Field               Label"
    ]
    for s in r.snapshots:
        lines.append(f"{s.sequence:>3}   {str(s.changed_person_id or '-'):>6}   {(s.changed_field or '-'):19} {s.label}")
    if r.warnings:
        lines += ["","Warnings","--------",*[f"- {w}" for w in r.warnings]]
    return "\n".join(lines)

def format_validation(vals):
    lines=[
        "Probe Validation",
        "================",
        "Status  Files  Person IDs     Hits      Package"
    ]
    for v in vals:
        status="PASS" if v.valid else "FAIL"
        ids=",".join(map(str,v.known_person_ids_found)) or "-"
        lines.append(f"{status:<6} {v.package_file_count:>5}  {ids:<13} {v.person_id_hit_count:>8}  {v.package}")
    return "\n".join(lines)

def format_regression(r):
    lines=[
        "Probe Regression",
        "================",
        f"Manifest                     {r.manifest}",
        f"Snapshots                    {r.snapshot_count}",
        f"Navigation verdict           {r.navigation_verdict}",
        f"Result                       {'PASS' if r.passed else 'FAIL'}",
        "",
        format_validation(r.validations),
        "",
        "Navigation",
        "----------",
        r.navigation_reason,
    ]
    return "\n".join(lines)
