"""Reunion Discovery Lab.

This package is intentionally separate from production parsing and Foundation
query features. Discovery code observes, compares, clusters, and reports;
confirmed findings are promoted into production decoders only after testing.
"""

from .console import DiscoveryConsole
from .event_scanner import EventObservation, EventScan, EventScanner, EventSignature, cluster_event_signatures, scan_event_observations
from .event_report import event_scan_markdown, format_event_scan, format_person_event_observations
from .field_archaeology import ByteStat, FieldArchaeologyReport, WordStat, analyse_observations, rank_constant_bytes, rank_variable_bytes
from .field_report import field_layout_markdown, format_layout, format_offset, format_unknown_fields
from .event_compare import EventComparison, EventComparisonReport, EventLayout, EventLayoutKey, LayoutDifference, LengthBucket, compare_layouts, discover_event_layouts, hexdump, observations_for_layout
from .event_compare_report import event_comparison_markdown, format_event_comparison, format_event_lengths, format_layout_diff, format_observation_hexdump
from .report import DiscoveryReport, default_report_path, package_report
from .scanner import PackageEntry, PackageScan, PackageScanner

__all__ = [
    "DiscoveryConsole",
    "EventObservation",
    "EventScan",
    "EventScanner",
    "EventSignature",
    "EventComparison",
    "EventComparisonReport",
    "EventLayout",
    "EventLayoutKey",
    "LayoutDifference",
    "LengthBucket",
    "ByteStat",
    "FieldArchaeologyReport",
    "WordStat",
    "DiscoveryReport",
    "PackageEntry",
    "PackageScan",
    "PackageScanner",
    "analyse_observations",
    "compare_layouts",
    "discover_event_layouts",
    "event_comparison_markdown",
    "format_event_comparison",
    "format_event_lengths",
    "format_layout_diff",
    "format_observation_hexdump",
    "hexdump",
    "observations_for_layout",
    "cluster_event_signatures",
    "field_layout_markdown",
    "format_layout",
    "format_offset",
    "format_unknown_fields",
    "rank_constant_bytes",
    "rank_variable_bytes",
    "default_report_path",
    "event_scan_markdown",
    "format_event_scan",
    "format_person_event_observations",
    "scan_event_observations",
    "package_report",
]

from .correlation_engine import (
    ByteCorrelation,
    GroupSummary,
    PropertyCorrelation,
    QualifierSummary,
    RankedObservation,
    StructuralMap,
    StructuralRegion,
    compare_people,
    correlate_groups,
    correlate_memo,
    correlate_place,
    qualifier_summaries,
    rank_observations,
    structural_map,
)
from .correlation_report import (
    archaeology_markdown,
    format_archaeology_dashboard,
    format_property_correlation,
    format_qualifier_analysis,
    format_ranked_observations,
    format_region_map,
)
