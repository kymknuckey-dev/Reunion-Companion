from reunion_companion.discovery.event_scanner import (
    EventObservation,
    EventScan,
    EventSignature,
)
from reunion_companion.discovery.event_report import (
    event_scan_markdown,
    format_event_scan,
    format_person_event_observations,
)


def _scan() -> EventScan:
    observation = EventObservation(
        person_id=1,
        person_name="Test Probe",
        record_offset=100,
        record_length=200,
        marker_offset=50,
        raw_date_offset=57,
        date_display="2 Jan 1925",
        qualifier=0,
        place_token="[[pt:1]]",
        memo_candidate=True,
        signature="aa bb",
        context_hex="00 11 22",
    )
    return EventScan(
        package_path="/tmp/Probe.familyfile14",
        main_data_size=1000,
        named_person_records=1,
        observations=(observation,),
        signatures=(
            EventSignature(
                signature="aa bb",
                count=1,
                sample_person_ids=(1,),
                sample_dates=("2 Jan 1925",),
            ),
        ),
    )


def test_format_event_scan() -> None:
    output = format_event_scan(_scan())
    assert "Date observations" in output
    assert "Unique signatures" in output
    assert "aa bb" in output


def test_format_person_observation() -> None:
    output = format_person_event_observations(list(_scan().observations), 1)
    assert "Test Probe" in output
    assert "2 Jan 1925" in output
    assert "[[pt:1]]" in output


def test_event_scan_markdown() -> None:
    output = event_scan_markdown(_scan())
    assert "# Reunion Raw Event Scan" in output
    assert "| 1 | `aa bb` |" in output
