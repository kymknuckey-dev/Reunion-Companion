from pathlib import Path

import reunion_companion.discovery.console as console_module


class _FakeDatabase:
    object_counts = {
        "people": 3,
        "families": 1,
        "events": 2,
        "places": 1,
        "notes": 0,
        "media": 0,
        "sources": 0,
        "citations": 0,
    }

    class _Event:
        def __init__(self, event_type):
            self.event_type = event_type

    events = [_Event("birth"), _Event("marriage")]


def test_console_commands(tmp_path: Path, monkeypatch) -> None:
    package = tmp_path / "Probe.familyfile14"
    package.mkdir()
    (package / "data").write_bytes(b"abc")

    monkeypatch.setattr(console_module, "from_package", lambda path: _FakeDatabase())
    console = console_module.DiscoveryConsole(package)

    assert "Files" in console.command("package")
    assert "People" in console.command("records")
    assert "birth" in console.command("events")
    assert "Commands:" in console.command("help")


def test_console_event_scan_commands(tmp_path: Path, monkeypatch) -> None:
    from reunion_companion.discovery.event_scanner import (
        EventObservation,
        EventScan,
        EventSignature,
    )

    package = tmp_path / "Probe.familyfile14"
    package.mkdir()
    (package / "data").write_bytes(b"abc")

    monkeypatch.setattr(console_module, "from_package", lambda path: _FakeDatabase())

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
        memo_candidate=False,
        signature="aa bb",
        context_hex="00 11",
    )
    fake_scan = EventScan(
        package_path=str(package),
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

    class _FakeEventScanner:
        def scan(self, path):
            return fake_scan

    monkeypatch.setattr(console_module, "EventScanner", _FakeEventScanner)
    console = console_module.DiscoveryConsole(package)

    assert "Date observations" in console.command("event-scan")
    assert "aa bb" in console.command("event-signatures")
    assert "Test Probe" in console.command("event-person 1")
    assert "Usage:" in console.command("event-person abc")


def test_console_field_archaeology_commands(tmp_path: Path, monkeypatch) -> None:
    from reunion_companion.discovery.event_scanner import (
        EventObservation,
        EventScan,
        EventSignature,
    )

    package = tmp_path / "Probe.familyfile14"
    package.mkdir()
    (package / "data").write_bytes(b"abc")

    monkeypatch.setattr(console_module, "from_package", lambda path: _FakeDatabase())

    context = bytes([0] * 24 + [10] * 24)
    observation = EventObservation(
        person_id=1,
        person_name="Test Probe",
        record_offset=0,
        record_length=100,
        marker_offset=24,
        raw_date_offset=31,
        date_display="1 Jan 1900",
        qualifier=0,
        place_token=None,
        memo_candidate=False,
        signature="aa bb",
        context_hex=context.hex(" "),
    )
    fake_scan = EventScan(
        package_path=str(package),
        main_data_size=1000,
        named_person_records=1,
        observations=(observation,),
        signatures=(
            EventSignature(
                signature="aa bb",
                count=1,
                sample_person_ids=(1,),
                sample_dates=("1 Jan 1900",),
            ),
        ),
    )

    class _FakeEventScanner:
        def scan(self, path):
            return fake_scan

    monkeypatch.setattr(console_module, "EventScanner", _FakeEventScanner)
    console = console_module.DiscoveryConsole(package)

    assert "Byte offsets relative to date marker" in console.command("birth-layout")
    assert "Byte Offset -1" in console.command("field-offset -1")
    assert "Field Archaeology Candidates" in console.command("unknown-fields")


def test_console_event_comparison_commands(tmp_path: Path, monkeypatch) -> None:
    from reunion_companion.discovery.event_scanner import (
        EventObservation,
        EventScan,
        EventSignature,
    )

    package = tmp_path / "Probe.familyfile14"
    package.mkdir()
    (package / "data").write_bytes(b"abc")

    monkeypatch.setattr(console_module, "from_package", lambda path: _FakeDatabase())

    observations = (
        EventObservation(
            person_id=1,
            person_name="Test Probe",
            record_offset=0,
            record_length=100,
            marker_offset=24,
            raw_date_offset=31,
            date_display="1 Jan 1900",
            qualifier=0,
            place_token=None,
            memo_candidate=False,
            signature="aa bb",
            context_hex=(bytes(range(48))).hex(" "),
        ),
        EventObservation(
            person_id=2,
            person_name="Mary Probe",
            record_offset=100,
            record_length=120,
            marker_offset=30,
            raw_date_offset=37,
            date_display="2 Jan 1900",
            qualifier=0,
            place_token="[[pt:1]]",
            memo_candidate=False,
            signature="aa bb",
            context_hex=(bytes(range(48))).hex(" "),
        ),
    )
    fake_scan = EventScan(
        package_path=str(package),
        main_data_size=1000,
        named_person_records=2,
        observations=observations,
        signatures=(
            EventSignature(
                signature="aa bb",
                count=2,
                sample_person_ids=(1, 2),
                sample_dates=("1 Jan 1900", "2 Jan 1900"),
            ),
        ),
    )

    class _FakeEventScanner:
        def scan(self, path):
            return fake_scan

    monkeypatch.setattr(console_module, "EventScanner", _FakeEventScanner)
    console = console_module.DiscoveryConsole(package)

    assert "Event Structure Comparison" in console.command("event-compare")
    assert "Event Layout 1" in console.command("event-layout 1")
    assert "Event Layout Diff" in console.command("event-diff 1 2")
    assert "Event Record Lengths" in console.command("event-lengths")
    assert "Hexdump" in console.command("event-hexdump 1")


def test_console_build5_correlation_commands(tmp_path: Path, monkeypatch) -> None:
    from reunion_companion.discovery.event_scanner import (
        EventObservation,
        EventScan,
        EventSignature,
    )

    package = tmp_path / "Probe.familyfile14"
    package.mkdir()
    (package / "data").write_bytes(b"abc")
    monkeypatch.setattr(console_module, "from_package", lambda path: _FakeDatabase())

    def observation(person_id, place=None, memo=False, qualifier=0, length=100, date="1 Jan 1900"):
        raw = bytearray([0] * 48)
        raw[24:30] = bytes.fromhex("0A 00 08 00 00 00")
        raw[30] = qualifier
        raw[31:35] = b"\x01\x02\x03\x04"
        if place:
            raw[38:43] = b"[[pt:"
        return EventObservation(
            person_id=person_id,
            person_name=f"Person {person_id}",
            record_offset=0,
            record_length=length,
            marker_offset=24,
            raw_date_offset=31,
            date_display=date,
            qualifier=qualifier,
            place_token=place,
            memo_candidate=memo,
            signature="01 00 00 00 00 00 00 00 06 00 00 00",
            context_hex=bytes(raw).hex(" "),
        )

    observations = (
        observation(1, place="[[pt:1]]", memo=True, length=300),
        observation(2, qualifier=0x80, length=100, date="1900"),
    )
    fake_scan = EventScan(
        package_path=str(package),
        main_data_size=1000,
        named_person_records=2,
        observations=observations,
        signatures=(
            EventSignature(
                signature="01 00 00 00 00 00 00 00 06 00 00 00",
                count=2,
                sample_person_ids=(1, 2),
                sample_dates=("1 Jan 1900", "1900"),
            ),
        ),
    )

    class _FakeEventScanner:
        def scan(self, path):
            return fake_scan

    monkeypatch.setattr(console_module, "EventScanner", _FakeEventScanner)
    console = console_module.DiscoveryConsole(package)

    assert "Archaeology Dashboard" in console.command("correlation")
    assert "Structural Correlation — place" in console.command("correlation-place")
    assert "memo candidate" in console.command("correlation-memo")
    assert "Date Qualifier Analysis" in console.command("qualifier-analysis")
    assert "Structural Region Map" in console.command("region-map")
    assert "Longest Observed Event Records" in console.command("longest-events")
    assert "Shortest Observed Event Records" in console.command("shortest-events")
    assert "person 1 vs 2" in console.command("compare-person 1 2")
    assert "Knowledge Status" in console.command("archaeology")


def test_console_build6_capture_commands(tmp_path: Path, monkeypatch) -> None:
    from reunion_companion.discovery.event_scanner import (
        EventObservation,
        EventScan,
        EventSignature,
    )

    package = tmp_path / "Probe.familyfile14"
    package.mkdir()
    (package / "data").write_bytes(b"abc")
    monkeypatch.setattr(console_module, "from_package", lambda path: _FakeDatabase())

    raw = bytearray(300)
    raw[64:70] = bytes.fromhex("0A 00 08 00 00 00")
    raw[78:88] = b"[[pt:123]]"

    observation = EventObservation(
        person_id=1,
        person_name="Test Probe",
        record_offset=0,
        record_length=300,
        marker_offset=64,
        raw_date_offset=71,
        date_display="1 Jan 1900",
        qualifier=0,
        place_token="[[pt:123]]",
        memo_candidate=False,
        signature="sig",
        context_hex=bytes(raw[40:88]).hex(" "),
        capture_start=0,
        capture_end=len(raw),
        capture_hex=bytes(raw).hex(" "),
        capture_truncated_left=False,
        capture_truncated_right=False,
    )

    fake_scan = EventScan(
        package_path=str(package),
        main_data_size=1000,
        named_person_records=1,
        observations=(observation,),
        signatures=(
            EventSignature(
                signature="sig",
                count=1,
                sample_person_ids=(1,),
                sample_dates=("1 Jan 1900",),
            ),
        ),
    )

    class _FakeEventScanner:
        def scan(self, path):
            return fake_scan

    monkeypatch.setattr(console_module, "EventScanner", _FakeEventScanner)
    console = console_module.DiscoveryConsole(package)

    assert "Full Event Capture Summary" in console.command("capture-summary")
    assert "Full Event Capture — Person 1" in console.command("capture-person 1")
    assert "[[pt:123]]" in console.command("capture-tokens")
    assert "Repeated Marker-relative Sequences" in console.command("capture-sequences")
    assert "Largest Full Event Captures" in console.command("capture-longest")


def test_console_build7_boundary_commands(tmp_path: Path, monkeypatch) -> None:
    from reunion_companion.discovery.event_scanner import (
        EventObservation,
        EventScan,
        EventSignature,
    )

    package = tmp_path / "Probe.familyfile14"
    package.mkdir()
    (package / "data").write_bytes(b"abc")
    monkeypatch.setattr(console_module, "from_package", lambda path: _FakeDatabase())

    raw = bytearray(240)
    raw[64:70] = bytes.fromhex("0A 00 08 00 00 00")
    raw[96:100] = bytes.fromhex("06 00 00 00")
    raw[104:110] = bytes.fromhex("0A 00 08 00 00 00")
    raw[160:164] = bytes.fromhex("06 00 00 00")
    raw[168:174] = bytes.fromhex("0A 00 08 00 00 00")

    observation = EventObservation(
        person_id=1,
        person_name="Test Probe",
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

    fake_scan = EventScan(
        package_path=str(package),
        main_data_size=1000,
        named_person_records=1,
        observations=(observation,),
        signatures=(
            EventSignature(
                signature="sig",
                count=1,
                sample_person_ids=(1,),
                sample_dates=("1 Jan 1900",),
            ),
        ),
    )

    class _FakeEventScanner:
        def scan(self, path):
            return fake_scan

    monkeypatch.setattr(console_module, "EventScanner", _FakeEventScanner)
    console = console_module.DiscoveryConsole(package)

    assert "Object Boundary Scanner Summary" in console.command("boundary-scan")
    assert "Object Boundary Map — Person 1" in console.command("boundary-person 1")
    assert "Recurring Boundary Signatures" in console.command("boundary-signatures")
    assert "Recurring Candidate Object Transitions" in console.command("boundary-transitions")


def test_console_build8_consolidation_commands(tmp_path: Path, monkeypatch) -> None:
    from reunion_companion.discovery.event_scanner import (
        EventObservation,
        EventScan,
        EventSignature,
    )

    package = tmp_path / "Probe.familyfile14"
    package.mkdir()
    (package / "data").write_bytes(b"abc")
    monkeypatch.setattr(console_module, "from_package", lambda path: _FakeDatabase())

    raw = bytearray(260)
    raw[64:70] = bytes.fromhex("0A 00 08 00 00 00")
    raw[96:100] = bytes.fromhex("06 00 00 00")
    raw[100:108] = bytes.fromhex("0B 00 16 00 EA 03 12 00")
    raw[112:118] = bytes.fromhex("0A 00 08 00 00 00")
    raw[176:180] = bytes.fromhex("06 00 00 00")
    raw[180:188] = bytes.fromhex("15 00 08 00 00 00 00 00")
    raw[192:198] = bytes.fromhex("0A 00 08 00 00 00")

    observation = EventObservation(
        person_id=1,
        person_name="Test Probe",
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

    fake_scan = EventScan(
        package_path=str(package),
        main_data_size=1000,
        named_person_records=1,
        observations=(observation,),
        signatures=(
            EventSignature(
                signature="sig",
                count=1,
                sample_person_ids=(1,),
                sample_dates=("1 Jan 1900",),
            ),
        ),
    )

    class _FakeEventScanner:
        def scan(self, path):
            return fake_scan

    monkeypatch.setattr(console_module, "EventScanner", _FakeEventScanner)
    console = console_module.DiscoveryConsole(package)

    assert "Object Boundary Consolidation Summary" in console.command("consolidate")
    assert "Consolidated Object Map — Person 1" in console.command("consolidate-person 1")
    assert "Consolidated Block Families" in console.command("block-families")
    assert "Consolidated Family Transitions" in console.command("family-transitions")


def test_console_build9_grammar_commands(tmp_path: Path, monkeypatch) -> None:
    from reunion_companion.discovery.event_scanner import (
        EventObservation,
        EventScan,
        EventSignature,
    )

    package = tmp_path / "Probe.familyfile14"
    package.mkdir()
    (package / "data").write_bytes(b"abc")
    monkeypatch.setattr(console_module, "from_package", lambda path: _FakeDatabase())

    raw = bytearray(340)
    raw[64:70] = bytes.fromhex("0A 00 08 00 00 00")
    raw[96:100] = bytes.fromhex("06 00 00 00")
    raw[100:108] = bytes.fromhex("0B 00 16 00 EA 03 12 00")
    raw[112:118] = bytes.fromhex("0A 00 08 00 00 00")
    raw[176:180] = bytes.fromhex("06 00 00 00")
    raw[180:188] = bytes.fromhex("15 00 08 00 00 00 00 00")
    raw[192:198] = bytes.fromhex("0A 00 08 00 00 00")
    raw[256:260] = bytes.fromhex("06 00 00 00")
    raw[260:268] = bytes.fromhex("15 00 14 00 00 00 00 00")
    raw[272:278] = bytes.fromhex("0A 00 08 00 00 00")

    observation = EventObservation(
        person_id=1,
        person_name="Test Probe",
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

    fake_scan = EventScan(
        package_path=str(package),
        main_data_size=1000,
        named_person_records=1,
        observations=(observation,),
        signatures=(
            EventSignature(
                signature="sig",
                count=1,
                sample_person_ids=(1,),
                sample_dates=("1 Jan 1900",),
            ),
        ),
    )

    class _FakeEventScanner:
        def scan(self, path):
            return fake_scan

    monkeypatch.setattr(console_module, "EventScanner", _FakeEventScanner)
    console = console_module.DiscoveryConsole(package)

    assert "Object Structural Grammar Summary" in console.command("grammar")
    assert "Neutral Grammar Classes" in console.command("grammar-classes")
    assert "Structural Grammar Rules" in console.command("grammar-rules")
    assert "Recurring Structural Motifs" in console.command("grammar-motifs")
    assert "Repeated-Class Patterns" in console.command("grammar-repeats")


def test_console_build10_graph_commands(tmp_path: Path, monkeypatch) -> None:
    from reunion_companion.discovery.event_scanner import (
        EventObservation,
        EventScan,
        EventSignature,
    )

    package = tmp_path / "Probe.familyfile14"
    package.mkdir()
    (package / "data").write_bytes(b"abc")
    monkeypatch.setattr(console_module, "from_package", lambda path: _FakeDatabase())

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

    observation = EventObservation(
        person_id=1,
        person_name="Test Probe",
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

    fake_scan = EventScan(
        package_path=str(package),
        main_data_size=1000,
        named_person_records=1,
        observations=(observation,),
        signatures=(
            EventSignature(
                signature="sig",
                count=1,
                sample_person_ids=(1,),
                sample_dates=("1 Jan 1900",),
            ),
        ),
    )

    class _FakeEventScanner:
        def scan(self, path):
            return fake_scan

    monkeypatch.setattr(console_module, "EventScanner", _FakeEventScanner)
    console = console_module.DiscoveryConsole(package)

    assert "Grammar Graph Summary" in console.command("graph")
    assert "Grammar Root Classes" in console.command("graph-roots")
    assert "Grammar Leaf Classes" in console.command("graph-leaves")
    assert "Grammar Hub Classes" in console.command("graph-hubs")
    assert "Weighted Grammar Edges" in console.command("graph-edges")
    assert "Successor Profiles" in console.command("graph-successors")
    assert "Grammar Graph Motifs" in console.command("graph-motifs")
    assert "Person Grammar Graph — ID 1" in console.command("graph-person 1")


def test_console_build11_classification_commands(tmp_path: Path, monkeypatch) -> None:
    from reunion_companion.discovery.event_scanner import (
        EventObservation,
        EventScan,
        EventSignature,
    )

    package = tmp_path / "Probe.familyfile14"
    package.mkdir()
    (package / "data").write_bytes(b"abc")
    monkeypatch.setattr(console_module, "from_package", lambda path: _FakeDatabase())

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

    observation = EventObservation(
        person_id=1,
        person_name="Test Probe",
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

    fake_scan = EventScan(
        package_path=str(package),
        main_data_size=1000,
        named_person_records=1,
        observations=(observation,),
        signatures=(
            EventSignature(
                signature="sig",
                count=1,
                sample_person_ids=(1,),
                sample_dates=("1 Jan 1900",),
            ),
        ),
    )

    class _FakeEventScanner:
        def scan(self, path):
            return fake_scan

    monkeypatch.setattr(console_module, "EventScanner", _FakeEventScanner)
    console = console_module.DiscoveryConsole(package)

    assert "Object Classification Summary" in console.command("classify")
    classes = console_module.object_classes(fake_scan.observations)
    class_id = classes[0].class_id
    assert "Stable Object Classes" in console.command("object-classes")
    assert "Object Class" in console.command(f"object-class {class_id}")
    assert "Object Map — Person 1" in console.command("object-map 1")
    assert "Object Class Clusters" in console.command("object-clusters")
    assert "Nearest Structural Classes" in console.command("object-similarity")


def test_console_build12_alignment_commands(tmp_path: Path, monkeypatch) -> None:
    from reunion_companion.discovery.event_scanner import (
        EventObservation,
        EventScan,
        EventSignature,
    )

    package = tmp_path / "Probe.familyfile14"
    package.mkdir()
    (package / "data").write_bytes(b"abc")
    monkeypatch.setattr(console_module, "from_package", lambda path: _FakeDatabase())

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

    observation = EventObservation(
        person_id=1,
        person_name="Test Probe",
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

    fake_scan = EventScan(
        package_path=str(package),
        main_data_size=1000,
        named_person_records=1,
        observations=(observation,),
        signatures=(
            EventSignature(
                signature="sig",
                count=1,
                sample_person_ids=(1,),
                sample_dates=("1 Jan 1900",),
            ),
        ),
    )

    class _FakeEventScanner:
        def scan(self, path):
            return fake_scan

    monkeypatch.setattr(console_module, "EventScanner", _FakeEventScanner)
    console = console_module.DiscoveryConsole(package)

    assert "Semantic Alignment Summary" in console.command("alignment")
    assert "Strongest Object-Class Alignments" in console.command("alignment-edges")
    classes = console_module.object_classes(fake_scan.observations)
    class_id = classes[0].class_id
    assert "Alignment Profile" in console.command(f"alignment-class {class_id}")
    assert "Object-Class Co-occurrence" in console.command("alignment-pairs")
    assert "Object-Class Graph" in console.command("object-graph")
    assert "Structural Object Families" in console.command("object-families")
    assert "Aligned Object Path — Person 1" in console.command("object-path 1")


def test_console_build13_probe_commands(tmp_path: Path, monkeypatch) -> None:
    from reunion_companion.discovery.event_scanner import (
        EventObservation,
        EventScan,
        EventSignature,
    )
    from reunion_companion.discovery.semantic_probe import (
        ProbeSnapshot,
        compare_snapshots,
    )

    package = tmp_path / "Probe.familyfile14"
    package.mkdir()
    (package / "data").write_bytes(b"abc")
    monkeypatch.setattr(console_module, "from_package", lambda path: _FakeDatabase())

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

    observation = EventObservation(
        person_id=1,
        person_name="Test Probe",
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
    fake_scan = EventScan(
        package_path=str(package),
        main_data_size=1000,
        named_person_records=1,
        observations=(observation,),
        signatures=(
            EventSignature(
                signature="sig",
                count=1,
                sample_person_ids=(1,),
                sample_dates=("1 Jan 1900",),
            ),
        ),
    )

    class _FakeEventScanner:
        def scan(self, path):
            return fake_scan

    monkeypatch.setattr(console_module, "EventScanner", _FakeEventScanner)
    console = console_module.DiscoveryConsole(package)

    assert "Semantic Probe Priority Plan" in console.command("probe-plan")
    assert "Semantic Probe Workflow" in console.command("probe-template")

    fake_result = compare_snapshots(
        ProbeSnapshot("Before.familyfile14", "b", 1, 1, 1, (("OC-A", 1),), ()),
        ProbeSnapshot("After.familyfile14", "a", 1, 2, 2, (("OC-A", 1), ("OC-X", 1)), ()),
        probe_id="interactive-probe",
        semantic_label="Occupation",
    )
    monkeypatch.setattr(console_module, "compare_packages", lambda *args, **kwargs: fake_result)
    text = console.command(
        'probe-compare "Occupation" "Before.familyfile14" "After.familyfile14"'
    )
    assert "Semantic Probe — interactive-probe" in text
