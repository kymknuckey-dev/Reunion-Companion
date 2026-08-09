"""Formatting for Build 14 differential semantic verification."""

from __future__ import annotations

from .differential_verification import DifferentialResult, PersonDifferential


def format_differential(result: DifferentialResult, *, span_limit: int = 50) -> str:
    lines = [
        "Differential Semantic Verification",
        "==================================",
        f"Declared change       {result.declared_change}",
        f"Before                {result.before_path}",
        f"After                 {result.after_path}",
        f"Raw data changed      {'yes' if result.raw_changed else 'no'}",
        f"Before size           {result.before_size:,}",
        f"After size            {result.after_size:,}",
        f"Changed spans         {len(result.byte_spans):,}",
        f"Changed before bytes  {result.changed_before_bytes:,}",
        f"Changed after bytes   {result.changed_after_bytes:,}",
        f"Decoded event changes {len(result.decoded_event_deltas):,}",
        f"Object class changes  {len(result.class_deltas):,}",
        f"Alignment changes     {len(result.edge_deltas):,}",
        "",
    ]

    if result.decoded_event_deltas:
        lines.extend(["Decoded Event Differences", "-------------------------"])
        for item in result.decoded_event_deltas:
            lines.extend(
                [
                    f"Person {item.person_id}: {item.person_name}",
                    f"  Date       {item.before_date or '-'} -> {item.after_date or '-'}",
                    f"  Place      {item.before_place or '-'} -> {item.after_place or '-'}",
                    f"  Qualifier  {item.before_qualifier} -> {item.after_qualifier}",
                    f"  Evidence   {item.likely_change}",
                ]
            )
        lines.append("")

    lines.extend(["Raw Byte Differences", "--------------------"])
    if not result.byte_spans:
        lines.append("(none)")
    else:
        for index, span in enumerate(result.byte_spans[:span_limit], start=1):
            lines.extend(
                [
                    f"[{index}] {span.tag}",
                    f"  Before  {span.before_start:,}..{span.before_end:,} ({span.before_length} bytes)",
                    f"  After   {span.after_start:,}..{span.after_end:,} ({span.after_length} bytes)",
                    f"  B hex   {span.before_hex or '(empty)'}",
                    f"  A hex   {span.after_hex or '(empty)'}",
                    f"  B text  {span.before_ascii or '(empty)'}",
                    f"  A text  {span.after_ascii or '(empty)'}",
                ]
            )
        if len(result.byte_spans) > span_limit:
            lines.append(f"... {len(result.byte_spans)-span_limit} more changed spans")

    lines.extend(["", "Structural Overlay", "------------------"])
    if not result.class_deltas and not result.edge_deltas:
        lines.extend(
            [
                "No Object Class or graph-count change was detected.",
                "This no longer means 'unchanged': raw/decoded differences above remain valid evidence.",
            ]
        )
    else:
        for class_id, before, after, delta in result.class_deltas[:30]:
            lines.append(f"Class {class_id}: {before} -> {after} ({delta:+d})")
        for source, target, before, after, delta in result.edge_deltas[:30]:
            lines.append(f"Edge {source} -> {target}: {before} -> {after} ({delta:+d})")

    lines.extend(
        [
            "",
            "Verification Boundary",
            "---------------------",
            "The declared semantic change is supplied by the researcher. Build 14 proves what bytes and decoded structures changed; repeated controlled probes are still required before semantic promotion.",
        ]
    )
    return "\n".join(lines)


def format_person_differential(person: PersonDifferential) -> str:
    lines = [
        f"Person Differential — {person.person_id}",
        "=" * 34,
        f"Name: {person.person_name}",
        f"Decoded event changes: {len(person.event_deltas)}",
        f"Nearby raw spans: {len(person.nearby_byte_spans)}",
        "",
    ]
    for item in person.event_deltas:
        lines.extend(
            [
                f"- {item.before_date or '-'} -> {item.after_date or '-'}",
                f"  place: {item.before_place or '-'} -> {item.after_place or '-'}",
                f"  evidence: {item.likely_change}",
            ]
        )
    return "\n".join(lines)


def differential_markdown(result: DifferentialResult) -> str:
    body = format_differential(result, span_limit=200)
    return "# Differential Semantic Verification\n\n```text\n" + body + "\n```\n"
