# FFD 2.0 RC1.0.11.2 — Unified Family Charts & HTML Book QA Pass 2

## Purpose

Refine the RC1.0.11 family-book presentation after real-family QA.

## Changes

- `Family & Descendants` remains the master family-chart presentation.
- Above the husband's immediate parents, the chart now shows the available direct paternal line as husband-and-wife couples, oldest first, using the same couple/tree presentation as the rest of the chart.
- `Spouse Family & Descendants` now uses the same master chart renderer rather than a separate boxed/context layout.
- The spouse chart is rooted in the incoming spouse's birth family and shows the spouse and siblings, their partners/marriages, and their children; traversal stops at those children.
- The two charts remain grouped together, with `Family & Descendants` first and `Spouse Family & Descendants` immediately after it.
- The scoped History Book HTML submit path now preserves the clicked `format=HTML` value before disabling the publish buttons, preventing fallback to the wrong output path.
- Existing RC1.0.10 multi-page PDF reproduction remains untouched.

## Acceptance

1. Main family chart shows direct paternal ancestor couples above Husband's Parents when recorded.
2. Spouse chart has the same layout vocabulary as the main chart.
3. Spouse collateral descendants stop at sibling children.
4. Main chart precedes spouse chart in the same chart group.
5. Create HTML produces the Professional Family History HTML, not a Research/person-report presentation.
6. Existing PDF/archive and descendant-tree regressions remain green.
