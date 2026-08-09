from reunion_companion.foundation import (
    FoundationCitation,
    FoundationDatabase,
    FoundationDiagnostics,
    FoundationEvent,
    FoundationMedia,
    FoundationNote,
    FoundationPerson,
    FoundationPlace,
    FoundationSource,
)


def _db() -> FoundationDatabase:
    db = FoundationDatabase(
        package_path="/tmp/Test.familyfile14",
        version="14+",
        warnings=["warning one", "warning two"],
    )

    place = db.add_place(
        FoundationPlace(object_id=1, name="Adelaide, South Australia")
    )
    person = db.add_person(
        FoundationPerson(
            object_id=1,
            given="Test",
            surname="Probe",
            display_name="Test Probe",
        )
    )
    other = db.add_person(
        FoundationPerson(
            object_id=2,
            given="Mary",
            surname="Probe",
            display_name="Mary Probe",
        )
    )

    birth = db.add_event(
        FoundationEvent(
            object_id=1,
            event_type="Birth",
            date_text="2 Jan 1925",
            place=place,
            memo="birth memo",
            owner_type="person",
            owner_id=1,
        )
    )
    person.events.append(birth)

    residence = db.add_event(
        FoundationEvent(
            object_id=2,
            event_type="Residence",
            place_text="Unresolved Place",
            owner_type="person",
            owner_id=2,
        )
    )
    other.events.append(residence)

    note = db.add_note(
        FoundationNote(
            object_id=1,
            note_type="person",
            text="A note",
            owner_type="person",
            owner_id=1,
        )
    )
    person.notes.append(note)

    source = db.add_source(
        FoundationSource(object_id=1, title="Birth Certificate")
    )
    citation = db.add_citation(
        FoundationCitation(
            object_id=1,
            source=source,
            source_id=1,
            source_title="Birth Certificate",
            owner_type="person",
            owner_id=1,
            event_id=1,
        )
    )
    birth.citations.append(citation)
    source.citations.append(citation)
    person.citations.append(citation)

    media = db.add_media(
        FoundationMedia(
            object_id=1,
            media_key="p1-photo",
            owner_type="person",
            owner_id=1,
            fingerprint="abc",
            filename="portrait.jpg",
            caption="Portrait",
            description=None,
        )
    )
    person.media.append(media)

    return db


def test_diagnostic_object_counts() -> None:
    report = FoundationDiagnostics(_db()).report()
    objects = report.section("Objects")

    assert objects.metrics["people"] == 2
    assert objects.metrics["events"] == 2
    assert objects.metrics["notes"] == 1
    assert objects.metrics["media"] == 1
    assert objects.metrics["sources"] == 1
    assert objects.metrics["citations"] == 1


def test_event_diagnostics_report_types_and_coverage() -> None:
    section = FoundationDiagnostics(_db()).event_section()

    assert section.metrics["total"] == 2
    assert section.metrics["types"] == 2
    assert section.metrics["with_dates"] == 1
    assert section.metrics["with_places"] == 2
    assert section.metrics["with_citations"] == 1
    assert section.metrics["unresolved_place_text"] == 1
    assert "Birth: 1" in section.details
    assert "Residence: 1" in section.details


def test_source_diagnostics_report_resolution() -> None:
    section = FoundationDiagnostics(_db()).source_section()

    assert section.metrics["sources"] == 1
    assert section.metrics["citations"] == 1
    assert section.metrics["resolved_citations"] == 1
    assert section.metrics["unresolved_citations"] == 0
    assert section.metrics["used_sources"] == 1


def test_note_diagnostics_report_owner_coverage() -> None:
    section = FoundationDiagnostics(_db()).note_section()

    assert section.metrics["notes"] == 1
    assert section.metrics["person_notes"] == 1
    assert section.metrics["family_notes"] == 0
    assert section.metrics["people_with_notes"] == 1


def test_media_diagnostics_report_metadata_coverage() -> None:
    section = FoundationDiagnostics(_db()).media_section()

    assert section.metrics["media"] == 1
    assert section.metrics["with_filename"] == 1
    assert section.metrics["with_caption"] == 1
    assert section.metrics["with_description"] == 0
    assert section.metrics["without_caption"] == 0
    assert section.metrics["without_description"] == 1


def test_warning_diagnostics_preserve_warning_text() -> None:
    section = FoundationDiagnostics(_db()).warning_section()

    assert section.metrics["count"] == 2
    assert section.details == ["warning one", "warning two"]
