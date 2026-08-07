from reunion_companion.foundation import FoundationBuilder
from reunion_companion.model import (
    Citation,
    Event,
    Family,
    Media,
    Note,
    Person,
    Place,
    ReunionDatabase,
    Source,
)


def _database() -> ReunionDatabase:
    event = Event(
        event_type="Birth",
        place_id=1,
        place="Adelaide, South Australia",
        memo="Birth memo",
        citations=[
            Citation(
                source_id=1,
                source_title="Birth Certificate",
                detail="Certificate 123",
                raw_offset=500,
            )
        ],
    )

    person = Person(
        id=1,
        given="Test",
        surname="Probe",
        display="Test Probe",
        sex="male",
        events=[event],
        notes=[
            Note(
                note_type="person",
                text="Test person note",
                raw_offset=400,
            )
        ],
    )

    family = Family(id=1, spouse_ids=[1], child_ids=[])

    source = Source(
        source_id=1,
        title="Birth Certificate",
        raw_offset=600,
    )

    media = Media(
        media_key="p1-test",
        owner_type="person",
        owner_id=1,
        fingerprint="abc123",
        filename="test.jpg",
        caption="Portrait",
        description="Test portrait",
    )
    person.media.append(media)

    return ReunionDatabase(
        package_path="/tmp/Test.familyfile14",
        version="14+",
        people={1: person},
        families={1: family},
        warnings=[],
        sources={1: source},
        places={1: Place(id=1, name="Adelaide, South Australia")},
        media={media.media_key: media},
    )


def test_builder_converts_notes_media_sources_and_citations() -> None:
    db, report = FoundationBuilder().build_with_report(_database())

    assert db.object_counts == {
        "people": 1,
        "families": 1,
        "events": 1,
        "places": 1,
        "notes": 1,
        "media": 1,
        "sources": 1,
        "citations": 1,
    }
    assert report.notes == 1
    assert report.media == 1
    assert report.sources == 1
    assert report.citations == 1


def test_note_is_attached_to_person() -> None:
    db = FoundationBuilder().build(_database())
    note = db.person(1).notes[0]

    assert note.text == "Test person note"
    assert note.owner_type == "person"
    assert note.owner_id == 1
    assert note.source_offset == 400


def test_media_is_attached_and_indexed() -> None:
    db = FoundationBuilder().build(_database())
    media = db.person(1).media[0]

    assert media.media_key == "p1-test"
    assert media.display_name == "test.jpg"
    assert media.has_metadata is True
    assert db.find_media_by_filename("TEST.JPG") == [media]


def test_source_and_citation_are_linked() -> None:
    db = FoundationBuilder().build(_database())
    source = db.source(1)
    citation = db.citation(1)
    event = db.event(1)

    assert citation.source is source
    assert citation.resolved is True
    assert citation.display_source == "Birth Certificate"
    assert citation.detail == "Certificate 123"
    assert event.citations == [citation]
    assert source.citations == [citation]
    assert db.person(1).citations == [citation]


def test_source_title_lookup_is_case_insensitive() -> None:
    db = FoundationBuilder().build(_database())
    source = db.source(1)

    assert db.find_sources_by_title("birth certificate") == [source]


def test_unresolved_citation_preserves_source_identity() -> None:
    source = _database()
    source.people[1].events[0].citations[0].source_id = 999
    source.people[1].events[0].citations[0].source_title = "Missing Source"

    db = FoundationBuilder().build(source)
    citation = db.citation(1)

    assert citation.source is None
    assert citation.resolved is False
    assert citation.source_id == 999
    assert citation.display_source == "Missing Source"
