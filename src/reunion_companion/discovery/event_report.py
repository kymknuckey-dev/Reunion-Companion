"""Markdown/text reports for raw event archaeology."""

from __future__ import annotations

from .event_scanner import EventObservation, EventScan


def format_event_scan(scan: EventScan, *, limit: int = 20) -> str:
    with_place = sum(1 for item in scan.observations if item.place_token)
    with_memo = sum(1 for item in scan.observations if item.memo_candidate)

    lines = [
        "Raw Event Scan",
        "--------------",
        f"Named person records     {scan.named_person_records:>10,}",
        f"Date observations        {scan.observation_count:>10,}",
        f"Unique signatures        {scan.signature_count:>10,}",
        f"With place token         {with_place:>10,}",
        f"With memo candidate      {with_memo:>10,}",
        "",
        "Top Signatures",
        "--------------",
    ]

    for index, cluster in enumerate(scan.signatures[:limit], start=1):
        ids = ", ".join(str(value) for value in cluster.sample_person_ids)
        dates = "; ".join(cluster.sample_dates)
        lines.extend(
            [
                f"{index:>2}. {cluster.count:>7,}  {cluster.signature or '(empty)'}",
                f"    people: {ids}",
                f"    dates:  {dates}",
            ]
        )

    if scan.signature_count > limit:
        lines.append(f"... {scan.signature_count - limit} more signatures")

    return "\n".join(lines)


def format_person_event_observations(
    observations: list[EventObservation],
    person_id: int,
) -> str:
    if not observations:
        return f"No raw date-bearing observations found for person ID {person_id}."

    lines = [
        f"Person Event Archaeology — ID {person_id}",
        "-" * 36,
        f"Name: {observations[0].person_name}",
        f"Observations: {len(observations)}",
        "",
    ]

    for index, item in enumerate(observations, start=1):
        lines.extend(
            [
                f"[{index}] Date: {item.date_display}",
                f"    absolute offset: {item.absolute_offset}",
                f"    record offset:   {item.record_offset}",
                f"    marker offset:   {item.marker_offset}",
                f"    qualifier:       {item.qualifier}",
                f"    place token:     {item.place_token or '-'}",
                f"    memo candidate:  {'yes' if item.memo_candidate else 'no'}",
                f"    signature:       {item.signature or '(empty)'}",
                f"    context:         {item.context_hex}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def event_scan_markdown(scan: EventScan) -> str:
    lines = [
        "# Reunion Raw Event Scan",
        "",
        f"- Package: `{scan.package_path}`",
        f"- Main data bytes: {scan.main_data_size:,}",
        f"- Named person records: {scan.named_person_records:,}",
        f"- Date observations: {scan.observation_count:,}",
        f"- Unique pre-date signatures: {scan.signature_count:,}",
        "",
        "## Signature clusters",
        "",
        "| Count | Signature | Sample people | Sample dates |",
        "|---:|---|---|---|",
    ]

    for cluster in scan.signatures:
        ids = ", ".join(str(value) for value in cluster.sample_person_ids)
        dates = "; ".join(cluster.sample_dates).replace("|", "\\|")
        signature = cluster.signature.replace("|", "\\|")
        lines.append(f"| {cluster.count} | `{signature}` | {ids} | {dates} |")

    return "\n".join(lines) + "\n"
