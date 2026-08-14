# FFD 1.9 Build 2.0.1 — Research/Presentation Biography Mode Separation

Corrective release for FFD 1.9 Build 2.

## Purpose

Make Biography rendering explicitly mode-aware so Research and Presentation cannot accidentally share the same output path during tests or rendering.

## Behaviour

- Research Biography preserves original imported Reunion notes, including paragraph/line-break structure.
- Presentation Biography uses the grounded Person Narrative service and its cache.
- Original notes are never replaced by generated prose.
- The Presentation Biography loading indicator is shown only on the narrative path.
- Build 2 narrative cache and source-fingerprint invalidation are retained.
- Research Home / Person Overview spacing refinements from Build 2 are retained.

## Regression hardening

`person_page` accepts an explicit presentation override for deterministic rendering/tests while normal UI routing continues to follow Companion's Presentation Mode state.

This prevents machine/user presentation-mode state from contaminating Research-mode regression tests.
