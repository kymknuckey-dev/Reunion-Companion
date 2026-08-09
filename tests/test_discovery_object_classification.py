from reunion_companion.discovery.event_scanner import EventObservation
from reunion_companion.discovery.object_classification import (
    classification_summary,
    classify_objects,
    cluster_classes,
    find_object_class,
    knowledge_document,
    nearest_classes,
    object_classes,
    person_object_map,
)


def _obs(person_id: int) -> EventObservation:
    raw = bytearray(420)
    raw[64:70] = bytes.fromhex("0A 00 08 00 00 00")
    raw[96:100] = bytes.fromhex("06 00 00 00")
    raw[100:108] = bytes.fromhex("0B 00 16 00 EA 03 12 00")
    raw[112:118] = bytes.fromhex("0A 00 08 00 00 00")
    raw[176:180] = bytes.fromhex("06 00 00 00")
    raw[180:188] = bytes.fromhex("15 00 08 00 00 00 00 00")
    raw[188:198] = b"HELLOWORLD"
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


def test_classification_is_deterministic() -> None:
    observations = [_obs(i) for i in range(30)]
    first = object_classes(observations)
    second = object_classes(observations)
    assert [x.class_id for x in first] == [x.class_id for x in second]
    assert [x.canonical_fingerprint for x in first] == [x.canonical_fingerprint for x in second]


def test_summary_classes_and_person_map() -> None:
    observations = [_obs(i) for i in range(30)]
    summary = classification_summary(observations)
    classes = object_classes(observations)
    objects = classify_objects(observations)
    assert summary.structural_objects == len(objects)
    assert summary.object_classes == len(classes)
    assert person_object_map(observations, 5)


def test_lookup_clusters_similarity_and_knowledge() -> None:
    observations = [_obs(i) for i in range(30)]
    classes = object_classes(observations)
    found = find_object_class(observations, classes[0].class_id)
    assert found == classes[0]
    assert cluster_classes(observations)
    assert isinstance(nearest_classes(observations), list)
    doc = knowledge_document(observations, source_package="/tmp/Probe.familyfile14")
    assert doc["build"] == 11
    assert doc["semantic_labels_assigned"] is False
    assert doc["classes"]
