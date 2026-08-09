from reunion_companion.discovery.classification_report import (
    classification_markdown,
    format_classification_summary,
    format_clusters,
    format_object_class,
    format_object_classes,
    format_person_object_map,
    format_similarity,
)
from reunion_companion.discovery.event_scanner import EventObservation
from reunion_companion.discovery.object_classification import (
    classification_summary,
    cluster_classes,
    nearest_classes,
    object_classes,
    person_object_map,
)


def _obs(person_id: int) -> EventObservation:
    raw = bytearray(340)
    raw[64:70] = bytes.fromhex("0A 00 08 00 00 00")
    raw[96:100] = bytes.fromhex("06 00 00 00")
    raw[100:108] = bytes.fromhex("0B 00 16 00 EA 03 12 00")
    raw[112:118] = bytes.fromhex("0A 00 08 00 00 00")
    raw[176:180] = bytes.fromhex("06 00 00 00")
    raw[180:188] = bytes.fromhex("15 00 08 00 00 00 00 00")
    raw[192:198] = bytes.fromhex("0A 00 08 00 00 00")
    raw[256:260] = bytes.fromhex("06 00 00 00")
    raw[260:268] = bytes.fromhex("0B 00 14 00 00 00 00 00")
    raw[272:278] = bytes.fromhex("0A 00 08 00 00 00")
    return EventObservation(
        person_id=person_id,
        person_name=f"Person {person_id}",
        record_offset=0,
        record_length=len(raw),
        marker_offset=64,
        raw_date_offset=71,
        date_display="1 Jan 1900",
        qualifier=0,
        place_token=None,
        memo_candidate=False,
        signature="sig",
        context_hex=bytes(raw[40:88]).hex(" "),
        capture_start=0,
        capture_end=len(raw),
        capture_hex=bytes(raw).hex(" "),
        capture_truncated_left=False,
        capture_truncated_right=False,
    )


def test_classification_formatters() -> None:
    observations = [_obs(i) for i in range(30)]
    summary = classification_summary(observations)
    classes = object_classes(observations)
    clusters = cluster_classes(observations)
    similar = nearest_classes(observations)
    mapped = person_object_map(observations, 1)

    assert "Object Classification Summary" in format_classification_summary(summary)
    assert "Stable Object Classes" in format_object_classes(classes)
    assert "Object Class" in format_object_class(classes[0])
    assert "Object Map — Person 1" in format_person_object_map(1, mapped)
    assert "Object Class Clusters" in format_clusters(clusters)
    assert "Nearest Structural Classes" in format_similarity(similar)

    report = classification_markdown(summary, classes, clusters, similar)
    assert "# Object Classification" in report
