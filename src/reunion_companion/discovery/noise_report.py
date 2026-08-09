"""Formatting for Build 15 semantic noise suppression."""
from __future__ import annotations


def format_suppressed_differential(item, *, semantic_limit=30, noise_limit=12, unknown_limit=20) -> str:
    r = item.result
    lines = [
        "Noise-Suppressed Differential Verification",
        "==========================================",
        f"Declared change       {r.declared_change}",
        f"Raw spans             {len(item.assessments):,}",
        f"Semantic candidates   {len(item.semantic_spans):,}",
        f"Suppressed noise      {len(item.noise_spans):,}",
        f"Unknown               {len(item.unknown_spans):,}",
        f"Suppression ratio     {item.suppression_ratio:.1%}",
        f"Decoded event changes {len(r.decoded_event_deltas):,}",
        f"Object class changes  {len(r.class_deltas):,}",
        f"Alignment changes     {len(r.edge_deltas):,}",
        "",
    ]
    if r.decoded_event_deltas:
        lines += ["Decoded Semantic Evidence", "-------------------------"]
        for e in r.decoded_event_deltas:
            lines += [
                f"Person {e.person_id}: {e.person_name}",
                f"  Date       {e.before_date or '-'} -> {e.after_date or '-'}",
                f"  Place      {e.before_place or '-'} -> {e.after_place or '-'}",
                f"  Evidence   {e.likely_change}",
            ]
        lines.append("")

    lines += ["Prioritised Semantic Spans", "--------------------------"]
    if not item.semantic_spans:
        lines.append("(none yet)")
    for a in item.semantic_spans[:semantic_limit]:
        s = a.span
        lines += [
            f"[{a.index}] {a.category} conf={a.confidence:.0%}",
            f"  reason  {a.reason}",
            f"  before  {s.before_start:,}..{s.before_end:,}",
            f"  after   {s.after_start:,}..{s.after_end:,}",
            f"  B text  {s.before_ascii}",
            f"  A text  {s.after_ascii}",
        ]
    if len(item.semantic_spans) > semantic_limit:
        lines.append(f"... {len(item.semantic_spans)-semantic_limit} more semantic candidates")

    lines += ["", "Suppressed Housekeeping", "-----------------------"]
    for a in item.noise_spans[:noise_limit]:
        lines.append(f"[{a.index}] {a.category} conf={a.confidence:.0%} — {a.reason}")
    if len(item.noise_spans) > noise_limit:
        lines.append(f"... {len(item.noise_spans)-noise_limit} more suppressed noise spans")

    lines += ["", "Unknown High-Priority Spans", "---------------------------"]
    for a in item.unknown_spans[:unknown_limit]:
        s = a.span
        lines.append(
            f"[{a.index}] {s.tag} B {s.before_start:,}..{s.before_end:,} "
            f"A {s.after_start:,}..{s.after_end:,} "
            f"({max(s.before_length, s.after_length)} bytes)"
        )
    if len(item.unknown_spans) > unknown_limit:
        lines.append(f"... {len(item.unknown_spans)-unknown_limit} more unknown spans")

    lines += [
        "", "Evidence Boundary", "-----------------",
        "Suppression changes reporting priority only. Raw Build 14 evidence is retained.",
    ]
    return "\n".join(lines)


def format_corpus_summary(results, patterns, summary) -> str:
    lines = [
        "Semantic Probe Corpus Analysis",
        "==============================",
        f"Probes                 {summary.probes}",
        f"ADD                    {summary.add_probes}",
        f"MODIFY                 {summary.modify_probes}",
        f"COMPOUND               {summary.compound_probes}",
        f"Raw spans              {summary.total_spans:,}",
        f"Suppressed noise       {summary.suppressed_noise_spans:,}",
        f"Semantic candidates    {summary.semantic_candidate_spans:,}",
        f"Unknown spans          {summary.unknown_spans:,}",
        f"Recurring patterns     {summary.recurring_patterns:,}",
        "",
        "Per Probe",
        "---------",
        "Probe                 Op        Raw   Semantic   Noise  Unknown  Decoded  Classes  Edges",
    ]
    for x in results:
        d, r = x.differential, x.differential.result
        lines.append(
            f"{x.spec.probe_id:<20} {x.spec.operation:<8} "
            f"{len(d.assessments):>5} {len(d.semantic_spans):>10} "
            f"{len(d.noise_spans):>7} {len(d.unknown_spans):>8} "
            f"{len(r.decoded_event_deltas):>8} {len(r.class_deltas):>8} "
            f"{len(r.edge_deltas):>6}"
        )
    lines += ["", "Most Recurrent Patterns", "-----------------------"]
    for p in patterns[:30]:
        lines.append(
            f"{p.recurrence:>6.1%}  {p.category:<22} "
            f"occ={p.occurrences:<5} probes={','.join(p.probes)}"
        )
    return "\n".join(lines)


def corpus_markdown(results, patterns, summary) -> str:
    return "# Semantic Noise Suppression & Probe Corpus\n\n```text\n" + format_corpus_summary(results, patterns, summary) + "\n```\n"
