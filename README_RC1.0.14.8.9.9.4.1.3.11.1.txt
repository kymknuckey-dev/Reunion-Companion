FFD 2.0 RC1.0.14.8.9.9.4.1.3.11.1 — Terminal Individual Opt-in Default

Purpose
-------
Terminal individuals remain visible and selectable in Family History scope,
but are no longer selected automatically.

Behaviour
---------
- Individual — no family branch rows remain available throughout the tree.
- Every terminal individual checkbox is OFF by default.
- The user explicitly selects only the individuals wanted in the report.
- Loaded/saved report configurations retain their explicit individual selections.
- Existing family chapter defaults and branch behaviour are unchanged.
- Established selector wording regression is preserved:
  "opening a branch does not include it"

QA
--
Targeted hierarchical scope, .3.9, .3.10, .3.11, .3.11.1 and packaging suite:
15 passed.
