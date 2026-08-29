## FFD 2.0 RC1.0.14.8.9.8.1 — Manage Presentation QA Correction

- Added presentation spacing between the Ryerson crawler status and its Start/Pause control.
- Added presentation spacing between the Recent crawler activity heading and its first activity row.
- Restyled Import History Previous/Next pagination to match the established Priorities-page pager.
- No crawler, queue, import, evidence, database, or pagination behaviour changed.

## FFD 2.0 RC1.0.14.8.9.8 — Manage Import History Pagination & Ryerson Running Activity Feedback

- Added a compact Recent crawler activity feed to Manage showing the three newest persisted Ryerson attempts across the internal queues.
- Activity rows show local time, person/search identity, plain-language status, and concise result/error feedback.
- Added Import History pagination at 10 entries per page, newest first, with Previous/Next controls.
- Activity display is read-only and causes no additional Ryerson requests.
- No crawler matching, queue lifecycle, retry, evidence-review, GEDCOM import, or database-schema behaviour changed.

## FFD 2.0 RC1.0.14.8.9.7.1.1 — Unified Crawler Regression Contract Correction

- Corrected the historical surname-bootstrap UI-route regression contract.
- The targeted start/pause POST routes remain present internally.
- Separate Targeted Bootstrap forms remain intentionally absent under the unified Ryerson Crawler UI.
- No crawler queue, matching, retry, browser, evidence, or lifecycle behaviour changed.

# FFD 2.0 RC1.0.10 — Multi-page PDF Reproduction

- All PDF source pages are required to render in order through PyMuPDF.
- Renderer exposes page-count/completeness metadata and rejects incomplete all-page rendering.
- Multi-page fitted-document publishing is regression tested.
- RC1.0.9 photograph geometry is frozen unchanged.

## RC1.0.9 Final Image Page Layout

- Accepted the final two-photo page layout as the canonical RC1.0.9 specification.
- Preserved the successful individual image sizes and horizontal centring.
- Shifted the complete two-photo group down 8 mm for balanced vertical placement.
- Added the approved page-layout visual reference and regression coverage.


## FFD 2.0 RC1.0.9 — Media Semantics & Book Presentation Pass 6
- Corrected two-photo page horizontal positioning by making each photo/caption card span the full printable width before centering its contents.
- Preserved the accepted Pass 5 image allowances: portrait/square 106mm and landscape 91mm, always `object-fit: contain` with no cropping.
- Removed publication links to original image/document/PDF files, including clickable PDF preview wrappers.
- Preserved Reunion preferred-photo semantics and family-event marriage-certificate publishing.
# Phase 3 — Build 17
## Database Architecture Reconstruction Foundation

Build 17 begins Phase 3 and converts Discovery into a versioned knowledge pipeline.

Added:
- immutable stage artifacts with input/payload hashes;
- Stage 16 canonical-region artifact;
- Stage 17 architecture snapshot;
- PRIMARY_CANDIDATE, STRUCTURAL_CANDIDATE, DERIVED_SAVE_STATE and UNRESOLVED roles;
- evidence-linked architectural relations;
- a small Build 17 console router instead of large console.py code injection.

Build 17 is a true delta over Build 16. The local project tree is now the source of truth.

Standalone regression: 3 passed.
Python syntax checks: passed.

## RC1.0.10 Multi-page PDF Reproduction QA Pass 1
Consistent maximum-fit document pages for multi-page PDFs; A4-optimised, aspect-ratio preserving, no crop.
## FFD 2.0 RC1.0.11 — Family-based Book Scope & Lineage Selection
Book publishing now supports an explicit family-scope workflow. The recorded paternal path supplies the default Book Sections; immediate sibling families remain contextual unless explicitly promoted. Incoming spouse ancestry/collateral information is chart-only and bounded. RC1.0.10 PDF geometry and the existing descendant tree are unchanged.

Regression validation: 783 tests passed across four bounded suite runs; critical RC1.0.10 PDF + Foundation archive + RC1.0.11 scope set: 24 passed.


## FFD 2.0 RC1.0.11.1 — Family Scope & Book Presentation QA Pass 1
Built from the validated RC1.0.11 family-scope baseline. RC1.0.10 PDF print geometry remains unchanged. QA adds progress feedback, bounded paternal-sibling child context, original-media links in HTML, and paired family/spouse chart presentation.

## FFD 2.0 RC1.0.11.2 — Unified Family Charts & HTML Book QA Pass 2

- Family & Descendants is now the master chart renderer for both the main family and incoming spouse family.
- Direct paternal ancestor couples are shown above Husband's Parents using the same couple/tree visual language.
- Spouse Family & Descendants is rooted at the spouse's birth family and uses the same natural family grouping.
- Spouse siblings may show partners/marriages and children; traversal stops at those children.
- Scoped History Book HTML selection now preserves the clicked HTML format before publish buttons are disabled.
- RC1.0.10 multi-page PDF reproduction code remains unchanged.
- Validation: 794 tests passed in four bounded full-suite chunks; focused publishing/PDF regression set 30 passed.
\n## RC1.0.11.3 Dual-Line Family Charts & HTML Parity QA Pass 3\n- Unified dual-line family presentation for main and spouse charts.\n- HTML History Books now assert both chart sections and both lineage sides.\n- Standalone deep Family & Descendants report remains future work.\n
## RC1.0.11.3.1 Spouse Family Chart Root Correction
- Corrected spouse-chart family semantics without changing the dual-line design or traversal boundary.

## RC1.0.11.3.2 Spouse Family-of-Origin Chart Correction
- Corrected spouse-context genealogy and aligned HTML/PDF presentation with the agreed book template.

## RC1.0.11.3.3 Unified Family Chart Presentation
- Visual unification only. No genealogy, scope, traversal, or spouse-chart changes.

## RC1.0.11.3.3.1 Spouse Lineage Stacking Correction
- Stacked the two spouse family-of-origin lineage sections vertically to match Family & Descendants.

## RC1.0.12 Standalone Descendant Report Pass 1
- New standalone descendant-report renderer with conventional Generation 1 starting-couple numbering and bounded generation depth.

## RC1.0.12.1 Descendant Report Preview Access Correction
- Corrected the missing normal-UI launch path for the RC1.0.12 report preview.

## RC1.0.12.2 Descendant Report Controls & Presentation QA
- Promoted the standalone Descendant Report from preview to a normal Publish workflow and fixed publishing-mark sizing.

## RC1.0.12.3 Publish & Descendant Report UX Cleanup
- Presentation/flow cleanup only: consistent Publish actions, family-aware Descendant Report launch and fixed-family configuration.

## RC1.0.12.4 Publish Report Tile Alignment & Iconography
- Presentation-only Publish refinement. No report-generation or genealogy changes.

## RC1.0.12.4.1 Publish Icon Column Alignment Correction
- Presentation-only alignment correction; no report or genealogy changes.

## RC1.0.12.4.2 Publish Tile DOM Alignment Correction
- Structural alignment fix: all Person Publishing tiles now share the same box model.

## RC1.0.12.4.3 Publish Families Duplication Removal
- Final RC1.0.12 cleanup: removed duplicate family-specific descendant-report launch UI.

## RC1.0.13 Navigation, Person Focus & Conversation UX Consolidation
- UI/interaction pass only; no relationship-resolution, genealogy or publishing changes.

## RC1.0.13.0.1 Person Context Mode-aware QA Correction
- QA-only correction for Presentation-mode independence.

## RC1.0.13.1 Persistent Global Navigation, Person Header Parity & Home Explore Removal
- UI navigation/parity pass only; no context-search, genealogy or publishing changes.

## RC1.0.13.1.1 Reports Person Header Parity
- Final UI parity correction for the RC1.0.13 navigation/person-context phase.
