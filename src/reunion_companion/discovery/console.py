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
from .object_classification import classification_summary, cluster_classes, find_object_class, knowledge_document, nearest_classes, object_classes, person_object_map
from .classification_report import classification_markdown, format_classification_summary, format_clusters, format_object_class, format_object_classes, format_person_object_map, format_similarity
from .semantic_alignment import alignment_edges, alignment_knowledge, alignment_profile, alignment_summary, cooccurrence_pairs, object_families, object_graph, person_object_path
from .alignment_report import alignment_markdown, format_alignment_edges, format_alignment_profile, format_alignment_summary, format_cooccurrence, format_object_families, format_object_graph, format_person_path, object_graph_dot
from .semantic_probe import compare_packages, evidence_document, rank_probe_targets, run_probe_manifest
from .probe_report import format_probe_plan, format_probe_result, format_semantic_evidence, manifest_markdown
from .differential_verification import compare_packages_differential, person_differential, result_document
from .differential_report import differential_markdown, format_differential, format_person_differential
from .noise_suppression import corpus_document, run_corpus_manifest, suppress_noise
from .noise_report import corpus_markdown, format_corpus_summary, format_suppressed_differential
from .canonical_regions import extract_region_corpus, region_document
from .canonical_region_report import canonical_region_markdown, format_region_map as format_canonical_region_map, format_region_overlaps as format_canonical_region_overlaps, format_region_probe as format_canonical_region_probe, format_region_summary as format_canonical_region_summary
from .build17_console import HELP as BUILD17_HELP, handle_build17_command
from .build18_1_console import handle_build18_1_command
from .build19_console import handle_build19_command
from .build20_console import handle_build20_command
from .build21_console import handle_build21_command
from .build22_console import handle_build22_command
from .build23_console import handle_build23_command
from .build24_console import handle_build24_command
from .scanner import PackageScanner


BANNER = """\
========================================================
 Reunion Discovery Lab — Phase 4 Build 24
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
  classify            Summarise Phase 2 structural object classification
  object-classes      Show deterministic structural object classes
  object-class ID     Inspect one structural object class
  object-map ID       Show classified object sequence for one person
  object-clusters     Show coarse clusters above stable object classes
  object-similarity   Show nearest structural object classes
  object-knowledge    Write machine-readable classification knowledge JSON
  object-report       Write object classification Markdown report
  alignment           Summarise Object Class alignment and graph evidence
  alignment-edges     Show strongest directed Object Class alignments
  alignment-class ID  Inspect neighbours/co-occurrence for one Object Class
  alignment-pairs     Show strongest person-level Object Class co-occurrence
  object-graph        Show central Object Classes in the alignment graph
  object-families     Show connected structural Object Class families
  object-path ID      Show aligned Object Class path for one person
  alignment-knowledge Write machine-readable alignment knowledge JSON
  alignment-dot       Write GraphViz Object Class graph
  alignment-report    Write Semantic Alignment Markdown report
  probe-plan          Rank important Object Classes for controlled probes
  probe-template      Show the Build 13 controlled-probe workflow/manifest format
  probe-compare ...   Compare BEFORE and AFTER packages for one declared change
  probe-batch FILE    Run a JSON probe manifest and aggregate semantic evidence
  probe-batch-report FILE Run manifest and write Markdown/JSON evidence reports
  probe-diff ...      Byte-level + decoded differential BEFORE/AFTER comparison
  probe-diff-report ... Run differential comparison and write Markdown/JSON reports
  probe-noise ...     Differential comparison with semantic-noise suppression
  probe-corpus FILE   Analyse all controlled probes from a corpus JSON manifest
  probe-corpus-report FILE Analyse corpus and write Markdown/JSON reports
  region-extract FILE Analyse corpus and extract canonical region candidates
  region-map FILE     Show canonical region candidate map
  region-probe ID FILE Show regions for one controlled probe
  region-overlap FILE Show shared region signatures
  region-report FILE  Write canonical_regions.md and semantic_regions.json
  pipeline-build FILE Build Stage 16/17 versioned knowledge artifacts
  architecture-summary FILE Show reconstructed architecture summary
  architecture-components FILE Show architecture components
  architecture-probe ID FILE Show evidence for one probe
  architecture-report FILE Write architecture report/snapshot and pipeline artifacts
  confidence-summary DIR Show Build 18.1 semantic-confidence summary
  confidence-probe ID DIR Show confidence for one semantic probe
  confidence-region CR-ID DIR Inspect one canonical-region confidence
  confidence-build DIR Write persistent Stage 18 confidence artifact
  confidence-report DIR Write semantic confidence reports/artifact
  dependency-summary DIR Show Build 19 region-dependency summary
  dependency-nodes DIR Show dependency graph nodes
  dependency-edges DIR Show dependency graph edges
  dependency-region CR-ID DIR Inspect one region dependency
  dependency-build DIR Write persistent Stage 19 dependency artifact
  dependency-report DIR Write dependency Markdown/JSON/artifact
  object-reconstruction-summary DIR Show Build 20 object reconstruction summary
  object-reconstruction-list DIR Show reconstructed logical objects
  object-reconstruction-detail ID DIR Inspect one reconstructed object
  object-reconstruction-build DIR Write persistent Stage 20 artifact
  object-reconstruction-report DIR Write object reconstruction Markdown/JSON/artifact
  instance-summary DIR Show Build 21 object-instance summary
  instance-list DIR Show reconstructed instance candidates
  instance-detail ID DIR Inspect one instance candidate
  instance-build DIR Write persistent Stage 21 artifact
  instance-report DIR Write instance reconstruction Markdown/JSON/artifact
  identity-summary DIR Show Build 22 identity archaeology summary
  identity-keys DIR Rank candidate identity keys
  identity-region CR-ID DIR Trace identity evidence for one region
  identity-build DIR Write persistent Stage 22 artifact
  identity-report DIR Write identity archaeology Markdown/JSON/artifact
  navigation-template Show Build 23 navigation-probe manifest template
  navigation-summary FILE Analyse Person Index/navigation evidence
  person-index-candidates FILE Rank candidate Person Index structures
  change-log-candidates FILE Rank candidate Change Log/navigation files
  navigation-delta LABEL FILE Inspect one controlled snapshot delta
  navigation-build FILE PIPELINE Write persistent Stage 23 artifact
  navigation-report FILE Write navigation archaeology Markdown/JSON
  probe-manifest DIR Discover probe snapshots and inferred metadata
  probe-manifest-write DIR [FILE] Generate navigation_probe.json automatically
  probe-validate FILE Validate all packages in a generated manifest
  probe-regression FILE Run validation + navigation regression
  probe-regression-report FILE Write regression Markdown/JSON
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
        raw_command = text.strip()
        command = raw_command.casefold()
        build17_result = handle_build17_command(self, raw_command, command, default_report_path)
        if build17_result is not None:
            return build17_result
        build18_1_result = handle_build18_1_command(self, raw_command, command, default_report_path)
        if build18_1_result is not None:
            return build18_1_result
        build19_result = handle_build19_command(self, raw_command, command, default_report_path)
        if build19_result is not None:
            return build19_result
        build20_result = handle_build20_command(self, raw_command, command, default_report_path)
        if build20_result is not None:
            return build20_result
        build21_result = handle_build21_command(self, raw_command, command, default_report_path)
        if build21_result is not None:
            return build21_result
        build22_result = handle_build22_command(self, raw_command, command, default_report_path)
        if build22_result is not None:
            return build22_result
        build23_result = handle_build23_command(self, raw_command, command, default_report_path)
        if build23_result is not None:
            return build23_result
        build24_result = handle_build24_command(self, raw_command, command, default_report_path)
        if build24_result is not None:
            return build24_result

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

        if command == "classify":
            return format_classification_summary(
                classification_summary(self._ensure_event_scan().observations)
            )

        if command == "object-classes":
            return format_object_classes(
                object_classes(self._ensure_event_scan().observations)
            )

        if command.startswith("object-class "):
            raw_id = command[len("object-class "):].strip()
            item = find_object_class(
                self._ensure_event_scan().observations,
                raw_id,
            )
            if item is None:
                return f"Object class not found: {raw_id}"
            return format_object_class(item)

        if command.startswith("object-map "):
            raw_id = command[len("object-map "):].strip()
            try:
                person_id = int(raw_id)
            except ValueError:
                return "Usage: object-map PERSON_ID"
            return format_person_object_map(
                person_id,
                person_object_map(
                    self._ensure_event_scan().observations,
                    person_id,
                ),
            )

        if command == "object-clusters":
            return format_clusters(
                cluster_classes(self._ensure_event_scan().observations)
            )

        if command == "object-similarity":
            return format_similarity(
                nearest_classes(self._ensure_event_scan().observations)
            )

        if command == "object-knowledge":
            target = default_report_path(
                self.package_path,
                "object_knowledge",
            ).with_suffix(".json")
            target.parent.mkdir(parents=True, exist_ok=True)
            document = knowledge_document(
                self._ensure_event_scan().observations,
                source_package=str(self.package_path),
            )
            target.write_text(
                __import__("json").dumps(document, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            return f"Object classification knowledge written: {target}"

        if command == "object-report":
            observations = self._ensure_event_scan().observations
            summary = classification_summary(observations)
            classes = object_classes(observations)
            clusters = cluster_classes(observations)
            similar = nearest_classes(observations)
            target = default_report_path(
                self.package_path,
                "object_classification",
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                classification_markdown(summary, classes, clusters, similar),
                encoding="utf-8",
            )
            return f"Object classification report written: {target}"

        if command == "alignment":
            return format_alignment_summary(
                alignment_summary(self._ensure_event_scan().observations)
            )

        if command == "alignment-edges":
            return format_alignment_edges(
                alignment_edges(self._ensure_event_scan().observations)
            )

        if command.startswith("alignment-class "):
            raw_id = command[len("alignment-class "):].strip()
            profile = alignment_profile(
                self._ensure_event_scan().observations,
                raw_id,
            )
            if profile is None:
                return f"Object class not found: {raw_id}"
            return format_alignment_profile(profile)

        if command == "alignment-pairs":
            return format_cooccurrence(
                cooccurrence_pairs(self._ensure_event_scan().observations)
            )

        if command == "object-graph":
            nodes, _ = object_graph(self._ensure_event_scan().observations)
            return format_object_graph(nodes)

        if command == "object-families":
            return format_object_families(
                object_families(self._ensure_event_scan().observations)
            )

        if command.startswith("object-path "):
            raw_id = command[len("object-path "):].strip()
            try:
                person_id = int(raw_id)
            except ValueError:
                return "Usage: object-path PERSON_ID"
            path = person_object_path(
                self._ensure_event_scan().observations,
                person_id,
            )
            if path is None:
                return f"No aligned object path found for person ID {person_id}."
            return format_person_path(path)

        if command == "alignment-knowledge":
            target = default_report_path(
                self.package_path,
                "semantic_alignment_knowledge",
            ).with_suffix(".json")
            target.parent.mkdir(parents=True, exist_ok=True)
            document = alignment_knowledge(
                self._ensure_event_scan().observations,
                source_package=str(self.package_path),
            )
            target.write_text(
                __import__("json").dumps(document, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            return f"Semantic alignment knowledge written: {target}"

        if command == "alignment-dot":
            observations = self._ensure_event_scan().observations
            nodes, edges = object_graph(observations)
            target = default_report_path(
                self.package_path,
                "semantic_alignment_graph",
            ).with_suffix(".dot")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                object_graph_dot(nodes, edges),
                encoding="utf-8",
            )
            return f"Semantic alignment GraphViz DOT written: {target}"

        if command == "alignment-report":
            observations = self._ensure_event_scan().observations
            summary = alignment_summary(observations)
            nodes, edges = object_graph(observations)
            families = object_families(observations)
            pairs = cooccurrence_pairs(observations)
            target = default_report_path(
                self.package_path,
                "semantic_alignment",
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                alignment_markdown(summary, nodes, edges, families, pairs),
                encoding="utf-8",
            )
            return f"Semantic alignment report written: {target}"

        if command == "probe-plan":
            return format_probe_plan(
                rank_probe_targets(self._ensure_event_scan().observations)
            )

        if command == "probe-template":
            return """Semantic Probe Workflow
=======================

Compare one controlled edit:
  probe-compare "Occupation" "/path/Before.familyfile14" "/path/After.familyfile14"

For repeated evidence, create a JSON manifest:
{
  "probes": [
    {
      "id": "occupation-01",
      "semantic_label": "Occupation",
      "before": "/path/Before1.familyfile14",
      "after": "/path/After1.familyfile14"
    },
    {
      "id": "occupation-02",
      "semantic_label": "Occupation",
      "before": "/path/Before2.familyfile14",
      "after": "/path/After2.familyfile14"
    }
  ]
}

Then:
  probe-batch "/path/probes.json"
  probe-batch-report "/path/probes.json"

Rule: change exactly one Reunion field/value per before/after pair.
"""

        if command.startswith("probe-compare "):
            import shlex
            try:
                parts = shlex.split(raw_command)
            except ValueError as exc:
                return f"Probe command parse error: {exc}"
            if len(parts) != 4:
                return (
                    'Usage: probe-compare "SEMANTIC LABEL" '
                    '"/path/BEFORE.familyfile14" "/path/AFTER.familyfile14"'
                )
            _, semantic_label, before_path, after_path = parts
            try:
                result = compare_packages(
                    before_path,
                    after_path,
                    probe_id="interactive-probe",
                    semantic_label=semantic_label,
                )
            except Exception as exc:
                return f"Probe comparison failed: {exc}"
            return format_probe_result(result)

        if command.startswith("probe-batch-report "):
            import shlex
            try:
                parts = shlex.split(raw_command)
            except ValueError as exc:
                return f"Probe command parse error: {exc}"
            if len(parts) != 2:
                return 'Usage: probe-batch-report "/path/probes.json"'
            manifest_path = parts[1]
            try:
                results, evidence = run_probe_manifest(manifest_path)
            except Exception as exc:
                return f"Probe manifest failed: {exc}"

            report_target = default_report_path(
                self.package_path,
                "semantic_probe_verification",
            )
            report_target.parent.mkdir(parents=True, exist_ok=True)
            report_target.write_text(
                manifest_markdown(results, evidence),
                encoding="utf-8",
            )

            json_target = report_target.with_name("semantic_probe_evidence.json")
            json_target.write_text(
                __import__("json").dumps(
                    evidence_document(
                        results,
                        evidence,
                        manifest_path=manifest_path,
                    ),
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            return (
                f"Semantic probe report written: {report_target}\n"
                f"Semantic probe evidence written: {json_target}"
            )

        if command.startswith("probe-batch "):
            import shlex
            try:
                parts = shlex.split(raw_command)
            except ValueError as exc:
                return f"Probe command parse error: {exc}"
            if len(parts) != 2:
                return 'Usage: probe-batch "/path/probes.json"'
            try:
                results, evidence = run_probe_manifest(parts[1])
            except Exception as exc:
                return f"Probe manifest failed: {exc}"
            sections = [format_probe_result(result, limit=15) for result in results]
            sections.append(format_semantic_evidence(evidence))
            return "\n\n".join(sections)

        if command.startswith("probe-diff-report "):
            import shlex
            try:
                parts = shlex.split(raw_command)
            except ValueError as exc:
                return f"Differential command parse error: {exc}"
            if len(parts) != 4:
                return ('Usage: probe-diff-report "SEMANTIC LABEL" '
                        '"/path/BEFORE.familyfile14" "/path/AFTER.familyfile14"')
            _, declared_change, before_path, after_path = parts
            try:
                result = compare_packages_differential(
                    before_path, after_path, declared_change=declared_change
                )
            except Exception as exc:
                return f"Differential comparison failed: {exc}"
            target = default_report_path(self.package_path, "differential_semantic_verification")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(differential_markdown(result), encoding="utf-8")
            json_target = target.with_suffix(".json")
            json_target.write_text(
                __import__("json").dumps(result_document(result), indent=2, sort_keys=True),
                encoding="utf-8",
            )
            return (f"Differential report written: {target}\n"
                    f"Differential JSON written: {json_target}")

        if command.startswith("probe-diff "):
            import shlex
            try:
                parts = shlex.split(raw_command)
            except ValueError as exc:
                return f"Differential command parse error: {exc}"
            if len(parts) != 4:
                return ('Usage: probe-diff "SEMANTIC LABEL" '
                        '"/path/BEFORE.familyfile14" "/path/AFTER.familyfile14"')
            _, declared_change, before_path, after_path = parts
            try:
                result = compare_packages_differential(
                    before_path, after_path, declared_change=declared_change
                )
            except Exception as exc:
                return f"Differential comparison failed: {exc}"
            return format_differential(result)

        if command.startswith("probe-corpus-report "):
            import shlex
            try:
                parts = shlex.split(raw_command)
            except ValueError as exc:
                return f"Corpus command parse error: {exc}"
            if len(parts) != 2:
                return 'Usage: probe-corpus-report "/path/probe_corpus.json"'
            try:
                results, patterns, summary = run_corpus_manifest(parts[1])
            except Exception as exc:
                return f"Probe corpus failed: {exc}"
            target = default_report_path(self.package_path, "semantic_noise_corpus")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(corpus_markdown(results, patterns, summary), encoding="utf-8")
            json_target = target.with_suffix(".json")
            json_target.write_text(
                __import__("json").dumps(corpus_document(results, patterns, summary), indent=2, sort_keys=True),
                encoding="utf-8",
            )
            return (f"Semantic noise corpus report written: {target}\n"
                    f"Semantic noise corpus JSON written: {json_target}")

        if command.startswith("probe-corpus "):
            import shlex
            try:
                parts = shlex.split(raw_command)
            except ValueError as exc:
                return f"Corpus command parse error: {exc}"
            if len(parts) != 2:
                return 'Usage: probe-corpus "/path/probe_corpus.json"'
            try:
                results, patterns, summary = run_corpus_manifest(parts[1])
            except Exception as exc:
                return f"Probe corpus failed: {exc}"
            return format_corpus_summary(results, patterns, summary)

        if command.startswith("probe-noise "):
            import shlex
            try:
                parts = shlex.split(raw_command)
            except ValueError as exc:
                return f"Noise command parse error: {exc}"
            if len(parts) != 4:
                return ('Usage: probe-noise "SEMANTIC LABEL" '
                        '"/path/BEFORE.familyfile14" "/path/AFTER.familyfile14"')
            _, declared_change, before_path, after_path = parts
            try:
                raw = compare_packages_differential(
                    before_path, after_path, declared_change=declared_change
                )
                result = suppress_noise(raw)
            except Exception as exc:
                return f"Noise-suppressed comparison failed: {exc}"
            return format_suppressed_differential(result)

        if command.startswith("region-report "):
            import shlex
            parts=shlex.split(raw_command)
            if len(parts)!=2:return 'Usage: region-report "/path/PROBE_CORPUS_KNUCKEY.json"'
            try: corpus=extract_region_corpus(parts[1])
            except Exception as exc:return f"Region extraction failed: {exc}"
            target=default_report_path(self.package_path,"canonical_regions")
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(canonical_region_markdown(corpus),encoding="utf-8")
            jt=target.with_name("semantic_regions.json")
            jt.write_text(__import__("json").dumps(region_document(corpus),indent=2,sort_keys=True),encoding="utf-8")
            return f"Canonical region report written: {target}\nSemantic region knowledge written: {jt}"

        if command.startswith("region-overlap "):
            import shlex
            parts=shlex.split(raw_command)
            if len(parts)!=2:return 'Usage: region-overlap "/path/PROBE_CORPUS_KNUCKEY.json"'
            try: corpus=extract_region_corpus(parts[1])
            except Exception as exc:return f"Region extraction failed: {exc}"
            return format_canonical_region_overlaps(corpus)

        if command.startswith("region-probe "):
            import shlex
            parts=shlex.split(raw_command)
            if len(parts)!=3:return 'Usage: region-probe PROBE_ID "/path/PROBE_CORPUS_KNUCKEY.json"'
            try: corpus=extract_region_corpus(parts[2])
            except Exception as exc:return f"Region extraction failed: {exc}"
            return format_canonical_region_probe(corpus,parts[1])

        if command.startswith("region-map "):
            import shlex
            parts=shlex.split(raw_command)
            if len(parts)!=2:return 'Usage: region-map "/path/PROBE_CORPUS_KNUCKEY.json"'
            try: corpus=extract_region_corpus(parts[1])
            except Exception as exc:return f"Region extraction failed: {exc}"
            return format_canonical_region_map(corpus)

        if command.startswith("region-extract "):
            import shlex
            parts=shlex.split(raw_command)
            if len(parts)!=2:return 'Usage: region-extract "/path/PROBE_CORPUS_KNUCKEY.json"'
            try: corpus=extract_region_corpus(parts[1])
            except Exception as exc:return f"Region extraction failed: {exc}"
            return format_canonical_region_summary(corpus)

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
