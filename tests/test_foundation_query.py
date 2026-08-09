from reunion_companion.foundation import (
    FoundationCitation,
    FoundationDatabase,
    FoundationEvent,
    FoundationMedia,
    FoundationPerson,
    FoundationPlace,
    FoundationQueryEngine,
)


def _db() -> FoundationDatabase:
    db = FoundationDatabase()

    adelaide = db.add_place(
        FoundationPlace(object_id=1, name="Adelaide, South Australia")
    )

    test = db.add_person(
        FoundationPerson(object_id=1, given="Test", surname="Probe", display_name="Test Probe")
    )
    mary = db.add_person(
        FoundationPerson(object_id=2, given="Mary", surname="Probe", display_name="Mary Probe")
    )

    birth = db.add_event(
        FoundationEvent(
            object_id=1,
            event_type="Birth",
            date_text="2 Jan 1925",
            place=adelaide,
            owner_type="person",
            owner_id=1,
        )
    )
    test.events.append(birth)

    unsourced_birth = db.add_event(
        FoundationEvent(
            object_id=2,
            event_type="Birth",
            date_text="1 Jan 1930",
            owner_type="person",
            owner_id=2,
        )
    )
    mary.events.append(unsourced_birth)

    citation = FoundationCitation(
        object_id=1,
        source_title="Birth Certificate",
        owner_type="person",
        owner_id=1,
        event_id=1,
    )
    birth.citations.append(citation)

    db.add_media(
        FoundationMedia(
            object_id=1,
            media_key="p1-photo",
            owner_type="person",
            owner_id=1,
            fingerprint="abc",
            filename="portrait.jpg",
            caption=None,
        )
    )

    return db


def test_people_search_partial_and_exact() -> None:
    engine = FoundationQueryEngine(_db())
    assert [p.id for p in engine.people("probe")] == [1, 2]
    assert [p.id for p in engine.people("Test Probe", exact=True)] == [1]


def test_person_resolves_unique_name() -> None:
    engine = FoundationQueryEngine(_db())
    assert engine.person("Mary Probe").id == 2
    assert engine.person("Probe") is None


def test_event_filters_type_and_place() -> None:
    engine = FoundationQueryEngine(_db())
    assert [e.id for e in engine.events(event_type="birth")] == [1, 2]
    assert [e.id for e in engine.events(event_type="birth", place="adelaide")] == [1]


def test_people_without_birth_source() -> None:
    engine = FoundationQueryEngine(_db())
    assert [p.id for p in engine.people_without_birth_source()] == [2]


def test_media_without_captions() -> None:
    engine = FoundationQueryEngine(_db())
    assert [m.id for m in engine.photos_without_captions()] == [1]
