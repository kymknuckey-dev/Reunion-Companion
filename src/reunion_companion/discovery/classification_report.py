"""Formatting for Phase 2 Build 11 object classification."""

from __future__ import annotations

from .object_classification import (
    ClassificationSummary,
    ObjectClassProfile,
    ObjectObservation,
    SimilarClass,
)


def format_classification_summary(summary: ClassificationSummary) -> str:
    return "\n".join(
        [
            "Object Classification Summary",
            "=============================",
            f"Source observations       {summary.observations:,}",
            f"Structural objects        {summary.structural_objects:,}",
            f"Stable object classes     {summary.object_classes:,}",
            f"Singleton classes         {summary.singleton_classes:,}",
            f"Mean class population     {summary.mean_class_population:.2f}",
            f"Mean class confidence     {summary.mean_confidence:.1%}",
            "",
            "Class IDs are deterministic structural fingerprints.",
            "No semantic Reunion labels are assigned.",
        ]
    )


def format_object_classes(classes: list[ObjectClassProfile], *, limit: int = 60) -> str:
    lines = [
        "Stable Object Classes",
        "=====================",
        "Class          Count  People  Length range  Conf   Place  ASCII  Date   Context",
    ]
    for item in classes[:limit]:
        prev = f"C{item.common_previous_class}" if item.common_previous_class else "-"
        nxt = f"C{item.common_next_class}" if item.common_next_class else "-"
        lines.append(
            f"{item.class_id:<14} {item.occurrences:>6,} {item.people:>7,} "
            f"{str(item.length_min)+'-'+str(item.length_max):>13} "
            f"{item.confidence:>6.1%} "
            f"{item.place_share:>6.0%} {item.ascii_share:>6.0%} "
            f"{item.date_share:>6.0%}   {prev}->{nxt}"
        )
    if len(classes) > limit:
        lines.append(f"... {len(classes)-limit} more classes")
    return "\n".join(lines)


def format_object_class(item: ObjectClassProfile) -> str:
    prev = f"C{item.common_previous_class}" if item.common_previous_class else "-"
    nxt = f"C{item.common_next_class}" if item.common_next_class else "-"
    lines = [
        f"Object Class {item.class_id}",
        "=" * (13 + len(item.class_id)),
        f"Fingerprint       {item.fingerprint_id}",
        f"Canonical         {item.canonical_fingerprint}",
        f"Occurrences       {item.occurrences:,}",
        f"People            {item.people:,}",
        f"Length            {item.length_min:,}-{item.length_max:,}",
        f"Mean / median     {item.length_mean:.2f} / {item.length_median:.2f}",
        f"Contains place    {item.place_share:.1%}",
        f"Contains ASCII    {item.ascii_share:.1%}",
        f"Contains date     {item.date_share:.1%}",
        f"Previous          {prev} ({item.common_previous_share:.1%})",
        f"Next              {nxt} ({item.common_next_share:.1%})",
        f"Confidence        {item.confidence:.1%}",
        "",
        "Sample people",
        "-------------",
        ", ".join(str(value) for value in item.sample_person_ids) or "-",
        "",
        "Sample previews",
        "---------------",
    ]
    lines.extend(f"- {preview or '(binary/no printable preview)'}" for preview in item.sample_previews)
    return "\n".join(lines)


def format_person_object_map(person_id: int, items: list[ObjectObservation]) -> str:
    lines = [
        f"Object Map — Person {person_id}",
        "=" * 30,
    ]
    if not items:
        lines.append("No classified objects found.")
        return "\n".join(lines)

    lines.extend(
        [
            f"Name: {items[0].person_name}",
            f"Date anchor: {items[0].date_display}",
            f"Objects: {len(items)}",
            "",
            "Index  Offset  Length  Class          Grammar  Preview",
        ]
    )
    for item in items:
        lines.append(
            f"{item.object_index:>5} {item.start_relative:>7} "
            f"{item.length:>7,}  OC-{item.fingerprint.fingerprint_id:<10} "
            f"C{item.fingerprint.grammar_class_id:<7} {item.ascii_preview[:48]}"
        )
    return "\n".join(lines)


def format_clusters(clusters: list[tuple[str, tuple[str, ...], int]], *, limit: int = 50) -> str:
    lines = [
        "Object Class Clusters",
        "=====================",
        "Cluster       Occurrences  Classes  Members",
    ]
    for cluster_id, classes, occurrences in clusters[:limit]:
        member_text = ", ".join(classes[:8]) + (" ..." if len(classes) > 8 else "")
        lines.append(
            f"{cluster_id:<13} {occurrences:>11,} {len(classes):>8}  {member_text}"
        )
    if len(clusters) > limit:
        lines.append(f"... {len(clusters)-limit} more clusters")
    return "\n".join(lines)


def format_similarity(items: list[SimilarClass], *, limit: int = 40) -> str:
    lines = [
        "Nearest Structural Classes",
        "==========================",
        "Similarity  Classes                         Shared / Different",
    ]
    for item in items[:limit]:
        lines.append(
            f"{item.similarity:>9.1%}  {item.left_class_id:<14} "
            f"{item.right_class_id:<14} "
            f"shared={','.join(item.shared_features)} "
            f"diff={','.join(item.differing_features)}"
        )
    if len(items) > limit:
        lines.append(f"... {len(items)-limit} more pairs")
    return "\n".join(lines)


def classification_markdown(
    summary: ClassificationSummary,
    classes: list[ObjectClassProfile],
    clusters: list[tuple[str, tuple[str, ...], int]],
    similar: list[SimilarClass],
) -> str:
    lines = [
        "# Object Classification",
        "",
        "## Summary",
        "",
        f"- Source observations: {summary.observations:,}",
        f"- Structural objects: {summary.structural_objects:,}",
        f"- Stable object classes: {summary.object_classes:,}",
        f"- Singleton classes: {summary.singleton_classes:,}",
        f"- Mean class population: {summary.mean_class_population:.2f}",
        f"- Mean class confidence: {summary.mean_confidence:.1%}",
        "",
        "## Classes",
        "",
        "| Class | Occurrences | People | Length | Confidence | Place | ASCII | Date |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in classes:
        lines.append(
            f"| {item.class_id} | {item.occurrences} | {item.people} | "
            f"{item.length_min}-{item.length_max} | {item.confidence:.1%} | "
            f"{item.place_share:.1%} | {item.ascii_share:.1%} | {item.date_share:.1%} |"
        )

    lines.extend(
        [
            "",
            "## Clusters",
            "",
            "| Cluster | Occurrences | Classes |",
            "|---|---:|---|",
        ]
    )
    for cluster_id, class_ids, occurrences in clusters:
        lines.append(
            f"| {cluster_id} | {occurrences} | {', '.join(class_ids)} |"
        )

    lines.extend(
        [
            "",
            "## Nearest structural classes",
            "",
            "| Similarity | Left | Right | Shared | Different |",
            "|---:|---|---|---|---|",
        ]
    )
    for item in similar:
        lines.append(
            f"| {item.similarity:.1%} | {item.left_class_id} | {item.right_class_id} | "
            f"{', '.join(item.shared_features)} | {', '.join(item.differing_features)} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "Build 11 assigns deterministic structural class IDs from measured fingerprints. "
            "These are not semantic Reunion field/event/fact/note/source names. Semantic promotion requires controlled evidence.",
        ]
    )
    return "\n".join(lines) + "\n"
