# FFD 2.0 RC1.0.12 — Standalone Descendant Report Pass 1

## Purpose

Create a standalone descendant report that is independent of History Book scope and presentation.

## Pass 1 workflow

1. Select a starting person.
2. Resolve or explicitly choose that person's spouse/family when needed.
3. Choose 1–6 generations (default 3).
4. Generate HTML or PDF.

Generation numbering follows normal genealogical convention:

- Generation 1 = starting couple
- Generation 2 = their children
- Generation 3 = grandchildren
- Generation 4 = great-grandchildren

## Presentation

The report uses an indented descendant-report structure rather than trying to fit a graphical tree onto one page.

- Starting couple receives the strongest visual emphasis.
- Names are primary.
- Birth/death dates are secondary.
- Spouses remain attached to their descendant.
- Family branches are indented and separated by simple rules and whitespace.
- No decorative colour dependency.
- The report flows naturally across A4 pages.
- HTML and PDF use the same source structure.

## Scope boundary

Pass 1 does not replace or alter the existing Publish Family Report control. For practical review, the existing per-family **Descendant Chart (HTML)** action is routed to the new standalone renderer at its existing default depth of four generations. A dedicated start-person/generation selector remains later work once the report presentation is accepted.

History Book paternal-line scope, spouse-family context, and embedded charts are untouched.
