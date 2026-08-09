"""Interactive Reunion Discovery Lab console.

Run:

    python -m reunion_companion.discovery.console "/path/to/file.familyfile14"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from reunion_companion.foundation import from_package

from .report import default_report_path, package_report
from .event_scanner import EventScanner
from .event_report import event_scan_markdown, format_event_scan, format_person_event_observations
from .field_archaeology import analyse_observations
from .field_report import field_layout_markdown, format_layout as format_field_layout, format_offset, format_unknown_fields
from .event_compare import compare_layouts, discover_event_layouts, observations_for_layout
from .event_compare_report import event_comparison_markdown, format_event_comparison, format_event_lengths, format_layout as format_event_layout, format_layout_diff, format_observation_hexdump
from .correlation_engine import compare_people, correlate_memo, correlate_place, qualifier_summaries, rank_observations, structural_map
from .correlation_report import archaeology_markdown, format_archaeology_dashboard, format_property_correlation, format_qualifier_analysis, format_ranked_observations, format_region_map
from .full_capture import capture_for_person, capture_summary, find_ascii_tokens, rank_capture_candidates, repeated_sequences
from .capture_report import capture_markdown, format_capture_candidates, format_capture_person, format_capture_summary, format_repeated_sequences, format_tokens
from .object_boundary import boundary_signatures, build_person_boundary_map, corpus_summary, transition_signatures
from .boundary_report import boundary_markdown, format_boundary_signatures, format_boundary_summary, format_person_boundaries, format_transitions
from .boundary_consolidation import build_consolidated_map, consolidation_summary, discover_block_families, discover_family_transitions
from .consolidation_report import consolidation_markdown, format_block_families, format_consolidated_person, format_consolidation_summary, format_family_transitions
from .structural_grammar import discover_grammar_classes, discover_grammar_rules, discover_repetition_patterns, discover_sequence_motifs, grammar_summary
from .grammar_report import format_grammar_classes, format_grammar_rules, format_grammar_summary, format_motifs, format_repetitions, grammar_markdown
from .grammar_graph import build_graph, discover_graph_motifs, graph_summary, graphviz_dot, hub_nodes, leaf_nodes, person_graph, root_nodes, successor_profiles
from .graph_report import format_edges, format_graph_motifs, format_graph_summary, format_hubs, format_leaves, format_person_graph, format_roots, format_successors, graph_markdown
from .scanner import PackageScanner


BANNER = """\
========================================================
 Reunion Discovery Lab — Beta 1 Build 10
========================================================
"""

HELP = """\
Commands:

  package             Show compact package inventory
  package-files       Show every package file
  records             Show current Foundation object counts
  events              Show currently decoded event types
  event-scan          Scan raw person records for date-bearing structures
  event-signatures    Show recurring pre-date binary signatures
  event-person ID     Inspect raw event observations for one person ID
  event-report        Write raw event scan Markdown report
  birth-layout        Analyse byte layout around all observed birth/date markers
  field-offset N      Inspect one byte offset relative to the date marker
  unknown-fields      Rank high-coverage variable and constant bytes
  field-report        Write field archaeology Markdown report
  event-compare       Discover and summarise recurring event layouts
  event-layout ID     Show one discovered layout
  event-diff A B      Compare two discovered layouts
  event-lengths       Show raw event record-length histogram
  event-hexdump ID N  Hexdump sample N from layout ID
  comparison-report   Write event comparison Markdown report
  correlation         Show structural correlation summary
  correlation-place   Correlate place presence with bytes/record shape
  correlation-memo    Correlate memo candidates with bytes/record shape
  qualifier-analysis  Analyse observed date qualifier values
  region-map          Show current evidence-based structural map
  longest-events      Rank largest observed event-bearing person records
  shortest-events     Rank smallest observed event-bearing person records
  compare-person A B  Compare first observations for two person IDs
  archaeology         Show master archaeology dashboard
  archaeology-report  Write structural archaeology Markdown report
  capture-summary     Show full bounded event-capture statistics
  capture-person ID   Show extended marker-relative capture for one person
  capture-tokens      Inventory ASCII reference tokens in extended captures
  capture-sequences   Rank repeated sequences beyond the old +23 boundary
  capture-longest     Rank largest records with capture sizes
  capture-report      Write full-capture Markdown report
  boundary-scan       Summarise candidate object boundaries across captures
  boundary-person ID  Show candidate boundaries/blocks for one person
  boundary-signatures Rank recurring candidate object-start signatures
  boundary-transitions Show recurring candidate block transitions
  boundary-report     Write candidate object-boundary Markdown report
  consolidate         Summarise Build 7 boundary consolidation
  consolidate-person ID Show consolidated blocks for one person
  block-families      Show neutral recurring block families
  family-transitions  Show transitions between consolidated block families
  consolidation-report Write boundary consolidation Markdown report
  grammar             Summarise neutral object structural grammar
  grammar-classes     Show higher-level neutral grammar classes
  grammar-rules       Show class-to-class structural rules
  grammar-motifs      Show recurring multi-class sequence motifs
  grammar-repeats     Show repeated-class/list-like patterns
  grammar-report      Write structural grammar Markdown report
  graph               Summarise weighted grammar graph
  graph-roots         Show most common root classes
  graph-leaves        Show most common leaf classes
  graph-hubs          Show structurally central classes
  graph-edges         Show weighted class-to-class edges
  graph-successors    Show mandatory and optional successor profiles
  graph-motifs        Show recurring graph motifs
  graph-person ID     Show grammar graph for one person
  graph-dot           Write GraphViz DOT graph
  graph-report        Write grammar graph Markdown report
  report              Write package discovery Markdown report
  help                Show this help
  quit                Exit

The event scanner observes and clusters binary structures. It does not assign
unknown event names until controlled probes or other evidence confirm them.
"""


class DiscoveryConsole:
    """Read-only discovery console around one Reunion package."""

    def __init__(self, package_path: str | Path) -> None:
        self.package_path = Path(package_path).expanduser()
        self.package_scan = PackageScanner().scan(self.package_path)
        self.database = from_package(self.package_path)
        self._event_scan = None
        self._field_report = None
        self._comparison_report = None
        self._place_correlation = None
        self._memo_correlation = None
        self._structural_map = None
        self._qualifier_summaries = None

    def _ensure_event_scan(self):
        if self._event_scan is None:
            self._event_scan = EventScanner().scan(self.package_path)
        return self._event_scan

    def _ensure_comparison(self):
        event_scan = self._ensure_event_scan()
        if self._comparison_report is None:
            self._comparison_report = discover_event_layouts(event_scan.observations)
        return self._comparison_report

    def _ensure_place_correlation(self):
        if self._place_correlation is None:
            self._place_correlation = correlate_place(self._ensure_event_scan().observations)
        return self._place_correlation

    def _ensure_memo_correlation(self):
        if self._memo_correlation is None:
            self._memo_correlation = correlate_memo(self._ensure_event_scan().observations)
        return self._memo_correlation

    def _ensure_structural_map(self):
        if self._structural_map is None:
            self._structural_map = structural_map(self._ensure_event_scan().observations)
        return self._structural_map

    def _ensure_qualifiers(self):
        if self._qualifier_summaries is None:
            self._qualifier_summaries = qualifier_summaries(self._ensure_event_scan().observations)
        return self._qualifier_summaries

    def command(self, text: str) -> str:
        command = text.strip().casefold()

        if command in {"help", "?"}:
            return HELP

        if command == "package":
            files = self.package_scan.files()
            thumbnails = [item for item in files if item.relative_path.startswith("thumbnails/")]
            caches = [item for item in files if item.suffix == ".cache"]
            main = [item for item in files if item.relative_path == "familyfile.familydata"]
            other = [
                item for item in files
                if item not in thumbnails and item not in caches and item not in main
            ]

            lines = [
                "Package",
                "-------",
                f"Path             {self.package_scan.package_path}",
                f"Files            {self.package_scan.file_count:,}",
                f"Directories      {self.package_scan.directory_count:,}",
                f"Bytes            {self.package_scan.total_bytes:,}",
                "",
                "Groups",
                "------",
                f"Main data        {len(main):>6,}",
                f"Cache files      {len(caches):>6,}",
                f"Thumbnails       {len(thumbnails):>6,}",
                f"Other files      {len(other):>6,}",
            ]
            if main:
                lines.append(f"Main data bytes  {main[0].size:>6,}")
            lines.append("")
            lines.append("Use 'package-files' for the complete file list.")
            return "\n".join(lines)

        if command in {"package-files", "scan"}:
            lines = [
                "Package Files",
                "-------------",
            ]
            lines.extend(
                f"{entry.relative_path:<50} {entry.size:>12,}"
                for entry in self.package_scan.files()
            )
            return "\n".join(lines)

        if command == "records":
            counts = self.database.object_counts
            lines = ["Foundation Objects", "------------------"]
            for name, value in counts.items():
                lines.append(f"{name.title():<12}{value:>10,}")
            return "\n".join(lines)

        if command == "events":
            counts: dict[str, int] = {}
            for event in self.database.events:
                key = (event.event_type or "(blank)").strip() or "(blank)"
                counts[key] = counts.get(key, 0) + 1

            lines = ["Decoded Event Types", "-------------------"]
            for name, value in sorted(
                counts.items(),
                key=lambda item: (-item[1], item[0].casefold()),
            ):
                lines.append(f"{name:<24}{value:>10,}")
            if not counts:
                lines.append("(none)")
            return "\n".join(lines)

        if command in {"event-scan", "event-signatures"}:
            if self._event_scan is None:
                self._event_scan = EventScanner().scan(self.package_path)
            return format_event_scan(
                self._event_scan,
                limit=50 if command == "event-signatures" else 20,
            )

        if command.startswith("event-person "):
            raw_id = command[len("event-person "):].strip()
            try:
                person_id = int(raw_id)
            except ValueError:
                return "Usage: event-person PERSON_ID"
            if self._event_scan is None:
                self._event_scan = EventScanner().scan(self.package_path)
            return format_person_event_observations(
                self._event_scan.for_person(person_id),
                person_id,
            )

        if command == "event-report":
            if self._event_scan is None:
                self._event_scan = EventScanner().scan(self.package_path)
            target = default_report_path(
                self.package_path,
                "events_raw",
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(event_scan_markdown(self._event_scan), encoding="utf-8")
            return f"Event report written: {target}"

        if command in {"birth-layout", "unknown-fields"}:
            if self._event_scan is None:
                self._event_scan = EventScanner().scan(self.package_path)
            if self._field_report is None:
                self._field_report = analyse_observations(self._event_scan.observations)
            if command == "birth-layout":
                return format_field_layout(self._field_report)
            return format_unknown_fields(self._field_report)

        if command.startswith("field-offset "):
            raw_offset = command[len("field-offset "):].strip()
            try:
                relative_offset = int(raw_offset, 0)
            except ValueError:
                return "Usage: field-offset OFFSET   (example: field-offset -12)"
            if self._event_scan is None:
                self._event_scan = EventScanner().scan(self.package_path)
            if self._field_report is None:
                self._field_report = analyse_observations(self._event_scan.observations)
            return format_offset(self._field_report, relative_offset)

        if command == "field-report":
            if self._event_scan is None:
                self._event_scan = EventScanner().scan(self.package_path)
            if self._field_report is None:
                self._field_report = analyse_observations(self._event_scan.observations)
            target = default_report_path(
                self.package_path,
                "field_archaeology",
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(field_layout_markdown(self._field_report), encoding="utf-8")
            return f"Field archaeology report written: {target}"

        if command == "event-compare":
            return format_event_comparison(self._ensure_comparison())

        if command.startswith("event-layout "):
            raw_id = command[len("event-layout "):].strip()
            try:
                layout_id = int(raw_id)
                layout = self._ensure_comparison().layout(layout_id)
            except (ValueError, KeyError):
                return "Usage: event-layout LAYOUT_ID"
            return format_event_layout(layout)

        if command.startswith("event-diff "):
            parts = command[len("event-diff "):].split()
            if len(parts) != 2:
                return "Usage: event-diff LEFT_ID RIGHT_ID"
            try:
                left_id, right_id = (int(value) for value in parts)
                report = self._ensure_comparison()
                left = report.layout(left_id)
                right = report.layout(right_id)
            except (ValueError, KeyError):
                return "Usage: event-diff LEFT_ID RIGHT_ID"
            return format_layout_diff(compare_layouts(left, right))

        if command == "event-lengths":
            return format_event_lengths(self._ensure_comparison())

        if command.startswith("event-hexdump "):
            parts = command[len("event-hexdump "):].split()
            if not 1 <= len(parts) <= 2:
                return "Usage: event-hexdump LAYOUT_ID [SAMPLE_NUMBER]"
            try:
                layout_id = int(parts[0])
                sample_number = int(parts[1]) if len(parts) == 2 else 1
                if sample_number < 1:
                    raise ValueError
                comparison = self._ensure_comparison()
                layout = comparison.layout(layout_id)
            except (ValueError, KeyError):
                return "Usage: event-hexdump LAYOUT_ID [SAMPLE_NUMBER]"
            observations = observations_for_layout(
                self._ensure_event_scan().observations,
                layout,
            )
            if sample_number > len(observations):
                return (
                    f"Layout {layout_id} has only {len(observations)} observations; "
                    f"sample {sample_number} is unavailable."
                )
            return format_observation_hexdump(observations[sample_number - 1])

        if command == "comparison-report":
            comparison = self._ensure_comparison()
            target = default_report_path(
                self.package_path,
                "event_comparison",
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(event_comparison_markdown(comparison), encoding="utf-8")
            return f"Event comparison report written: {target}"

        if command == "correlation":
            return "\n\n".join(
                [
                    format_archaeology_dashboard(
                        self._ensure_structural_map(),
                        self._ensure_place_correlation(),
                        self._ensure_memo_correlation(),
                        self._ensure_qualifiers(),
                    ),
                    format_property_correlation(self._ensure_place_correlation(), limit=10),
                    format_property_correlation(self._ensure_memo_correlation(), limit=10),
                ]
            )

        if command == "correlation-place":
            return format_property_correlation(self._ensure_place_correlation())

        if command == "correlation-memo":
            return format_property_correlation(self._ensure_memo_correlation())

        if command == "qualifier-analysis":
            return format_qualifier_analysis(self._ensure_qualifiers())

        if command == "region-map":
            return format_region_map(self._ensure_structural_map())

        if command == "longest-events":
            ranked = rank_observations(
                self._ensure_event_scan().observations,
                longest=True,
                limit=25,
            )
            return format_ranked_observations("Longest Observed Event Records", ranked)

        if command == "shortest-events":
            ranked = rank_observations(
                self._ensure_event_scan().observations,
                longest=False,
                limit=25,
            )
            return format_ranked_observations("Shortest Observed Event Records", ranked)

        if command.startswith("compare-person "):
            parts = command[len("compare-person "):].split()
            if len(parts) != 2:
                return "Usage: compare-person LEFT_PERSON_ID RIGHT_PERSON_ID"
            try:
                left_id, right_id = (int(value) for value in parts)
            except ValueError:
                return "Usage: compare-person LEFT_PERSON_ID RIGHT_PERSON_ID"
            result = compare_people(
                self._ensure_event_scan().observations,
                left_id,
                right_id,
            )
            if result is None:
                return (
                    f"Could not compare persons {left_id} and {right_id}: "
                    "one or both have no raw date-bearing observation."
                )
            return format_property_correlation(result, limit=24)

        if command == "archaeology":
            return format_archaeology_dashboard(
                self._ensure_structural_map(),
                self._ensure_place_correlation(),
                self._ensure_memo_correlation(),
                self._ensure_qualifiers(),
            )

        if command == "archaeology-report":
            target = default_report_path(
                self.package_path,
                "birth_structure",
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                archaeology_markdown(
                    self._ensure_structural_map(),
                    self._ensure_place_correlation(),
                    self._ensure_memo_correlation(),
                    self._ensure_qualifiers(),
                ),
                encoding="utf-8",
            )
            return f"Archaeology report written: {target}"

        if command == "capture-summary":
            return format_capture_summary(
                capture_summary(self._ensure_event_scan().observations)
            )

        if command.startswith("capture-person "):
            raw_id = command[len("capture-person "):].strip()
            try:
                person_id = int(raw_id)
            except ValueError:
                return "Usage: capture-person PERSON_ID"
            observation = capture_for_person(
                self._ensure_event_scan().observations,
                person_id,
            )
            if observation is None:
                return f"No captured event observation found for person ID {person_id}."
            return format_capture_person(observation)

        if command == "capture-tokens":
            return format_tokens(
                find_ascii_tokens(self._ensure_event_scan().observations)
            )

        if command == "capture-sequences":
            return format_repeated_sequences(
                repeated_sequences(self._ensure_event_scan().observations)
            )

        if command == "capture-longest":
            return format_capture_candidates(
                "Largest Full Event Captures",
                rank_capture_candidates(
                    self._ensure_event_scan().observations,
                    longest=True,
                    limit=25,
                ),
            )

        if command == "capture-report":
            event_scan = self._ensure_event_scan()
            summary = capture_summary(event_scan.observations)
            tokens = find_ascii_tokens(event_scan.observations)
            sequences = repeated_sequences(event_scan.observations)
            target = default_report_path(
                self.package_path,
                "full_event_capture",
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                capture_markdown(summary, tokens, sequences),
                encoding="utf-8",
            )
            return f"Full capture report written: {target}"

        if command == "boundary-scan":
            return format_boundary_summary(
                corpus_summary(self._ensure_event_scan().observations)
            )

        if command.startswith("boundary-person "):
            raw_id = command[len("boundary-person "):].strip()
            try:
                person_id = int(raw_id)
            except ValueError:
                return "Usage: boundary-person PERSON_ID"
            observation = capture_for_person(
                self._ensure_event_scan().observations,
                person_id,
            )
            if observation is None:
                return f"No captured event observation found for person ID {person_id}."
            return format_person_boundaries(
                build_person_boundary_map(observation)
            )

        if command == "boundary-signatures":
            return format_boundary_signatures(
                boundary_signatures(self._ensure_event_scan().observations)
            )

        if command == "boundary-transitions":
            return format_transitions(
                transition_signatures(self._ensure_event_scan().observations)
            )

        if command == "boundary-report":
            observations = self._ensure_event_scan().observations
            summary = corpus_summary(observations)
            signatures = boundary_signatures(observations)
            transitions = transition_signatures(observations)
            target = default_report_path(
                self.package_path,
                "object_boundaries",
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                boundary_markdown(summary, signatures, transitions),
                encoding="utf-8",
            )
            return f"Object boundary report written: {target}"

        if command == "consolidate":
            return format_consolidation_summary(
                consolidation_summary(self._ensure_event_scan().observations)
            )

        if command.startswith("consolidate-person "):
            raw_id = command[len("consolidate-person "):].strip()
            try:
                person_id = int(raw_id)
            except ValueError:
                return "Usage: consolidate-person PERSON_ID"
            observation = capture_for_person(
                self._ensure_event_scan().observations,
                person_id,
            )
            if observation is None:
                return f"No captured event observation found for person ID {person_id}."
            return format_consolidated_person(
                build_consolidated_map(observation)
            )

        if command == "block-families":
            families, _ = discover_block_families(
                self._ensure_event_scan().observations
            )
            return format_block_families(families)

        if command == "family-transitions":
            return format_family_transitions(
                discover_family_transitions(
                    self._ensure_event_scan().observations
                )
            )

        if command == "consolidation-report":
            observations = self._ensure_event_scan().observations
            summary = consolidation_summary(observations)
            families, _ = discover_block_families(observations)
            transitions = discover_family_transitions(observations)
            target = default_report_path(
                self.package_path,
                "boundary_consolidation",
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                consolidation_markdown(summary, families, transitions),
                encoding="utf-8",
            )
            return f"Boundary consolidation report written: {target}"

        if command == "grammar":
            return format_grammar_summary(
                grammar_summary(self._ensure_event_scan().observations)
            )

        if command == "grammar-classes":
            classes, _ = discover_grammar_classes(
                self._ensure_event_scan().observations
            )
            return format_grammar_classes(classes)

        if command == "grammar-rules":
            return format_grammar_rules(
                discover_grammar_rules(
                    self._ensure_event_scan().observations
                )
            )

        if command == "grammar-motifs":
            return format_motifs(
                discover_sequence_motifs(
                    self._ensure_event_scan().observations
                )
            )

        if command == "grammar-repeats":
            return format_repetitions(
                discover_repetition_patterns(
                    self._ensure_event_scan().observations
                )
            )

        if command == "grammar-report":
            observations = self._ensure_event_scan().observations
            summary = grammar_summary(observations)
            classes, _ = discover_grammar_classes(observations)
            rules = discover_grammar_rules(observations)
            motifs = discover_sequence_motifs(observations)
            repetitions = discover_repetition_patterns(observations)
            target = default_report_path(
                self.package_path,
                "structural_grammar",
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                grammar_markdown(summary, classes, rules, motifs, repetitions),
                encoding="utf-8",
            )
            return f"Structural grammar report written: {target}"

        if command == "graph":
            return format_graph_summary(
                graph_summary(self._ensure_event_scan().observations)
            )

        if command == "graph-roots":
            return format_roots(
                root_nodes(self._ensure_event_scan().observations)
            )

        if command == "graph-leaves":
            return format_leaves(
                leaf_nodes(self._ensure_event_scan().observations)
            )

        if command == "graph-hubs":
            return format_hubs(
                hub_nodes(self._ensure_event_scan().observations)
            )

        if command == "graph-edges":
            _, edges = build_graph(self._ensure_event_scan().observations)
            return format_edges(edges)

        if command == "graph-successors":
            return format_successors(
                successor_profiles(self._ensure_event_scan().observations)
            )

        if command == "graph-motifs":
            return format_graph_motifs(
                discover_graph_motifs(self._ensure_event_scan().observations)
            )

        if command.startswith("graph-person "):
            raw_id = command[len("graph-person "):].strip()
            try:
                person_id = int(raw_id)
            except ValueError:
                return "Usage: graph-person PERSON_ID"
            graph = person_graph(
                self._ensure_event_scan().observations,
                person_id,
            )
            if graph is None:
                return f"No grammar sequence found for person ID {person_id}."
            return format_person_graph(graph)

        if command == "graph-dot":
            target = default_report_path(
                self.package_path,
                "grammar_graph",
            ).with_suffix(".dot")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                graphviz_dot(self._ensure_event_scan().observations),
                encoding="utf-8",
            )
            return f"GraphViz DOT written: {target}"

        if command == "graph-report":
            observations = self._ensure_event_scan().observations
            summary = graph_summary(observations)
            nodes, edges = build_graph(observations)
            profiles = successor_profiles(observations)
            motifs = discover_graph_motifs(observations)
            target = default_report_path(
                self.package_path,
                "grammar_graph",
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                graph_markdown(summary, nodes, edges, profiles, motifs),
                encoding="utf-8",
            )
            return f"Grammar graph report written: {target}"

        if command == "report":
            target = default_report_path(
                self.package_path,
                "package",
            )
            package_report(self.package_scan).write(target)
            return f"Report written: {target}"

        if not command:
            return ""

        return f"Unknown command: {text!r}. Type 'help'."

    def run(self) -> int:
        print(BANNER)
        print(f"Opening:\n{self.package_path}\n")
        print("✓ Package scan complete")
        print("✓ Foundation build complete\n")
        print(HELP)

        while True:
            try:
                text = input("discover> ")
            except (EOFError, KeyboardInterrupt):
                print()
                return 0

            if text.strip().casefold() in {"quit", "exit", "q"}:
                return 0

            output = self.command(text)
            if output:
                print(output)
                print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="reunion-discover",
        description="Read-only Reunion Discovery Lab",
    )
    parser.add_argument("package", help="Path to a Reunion package")
    args = parser.parse_args(argv)

    try:
        return DiscoveryConsole(args.package).run()
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
