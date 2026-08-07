from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Evidence:
    """Describes how confidently a semantic value was decoded.

    `status` is intentionally a plain string so exported JSON remains simple.
    Common values are:
      - decoded
      - decoded-controlled-probes
      - inferred
      - unresolved
      - experimental
    """

    status: str = "decoded-controlled-probes"
    method: str | None = None
    note: str | None = None
