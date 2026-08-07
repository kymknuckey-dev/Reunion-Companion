"""Convenience adapter functions for Foundation Layer Alpha 4."""

from __future__ import annotations

from pathlib import Path

from reunion_companion.domain import load_reunion_database
from reunion_companion.model import ReunionDatabase

from .builder import FoundationBuilder
from .database import FoundationDatabase


def from_semantic_database(source: ReunionDatabase) -> FoundationDatabase:
    """Build a Foundation database from the verified semantic model."""
    return FoundationBuilder().build(source)


def from_package(package_path: str | Path) -> FoundationDatabase:
    """Load a Reunion package through the existing decoder, then adapt it.

    Alpha 4 deliberately does not decode the binary package itself.
    """
    semantic = load_reunion_database(package_path)
    return FoundationBuilder().build(semantic)
