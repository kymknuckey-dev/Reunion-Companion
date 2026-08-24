# FFD 2.0 RC1.0.12.4.2 — Publish Tile DOM Alignment Correction

## Purpose

Correct persistent Publish icon-column misalignment by removing the form-vs-link DOM difference.

## Rule

All five Person Publishing actions now use the same structure:

`form.publish-action-form > button.publish-action > icon + text + chevron`

This applies to:
- Research Profile
- Biography
- Person Report
- Descendant Report
- Configure Family-history Book

Descendant Report and Family-history Book use GET forms so navigation behaviour remains unchanged.

The same fixed 42 px icon column, text column and chevron column therefore comes from the same button box model for every tile.

The existing icon artwork and Descendant optical centring are retained.

No report, genealogy, scope or output behaviour changes.
