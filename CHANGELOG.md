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

## FFD 2.0 RC1.0.10 — Multi-page PDF Reproduction

- Hardened PDF page reproduction so the rendered page set must match the source PDF page count.
- Added explicit `page_count` and `all_pages_rendered` renderer metadata.
- Added multi-page person-document publishing regression coverage while preserving single-page certificate and image-page behaviour.

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
# Changelog

## Core Engine Build 1C

- Added model package exports
- Added model exceptions
- Added initial model test
- Commit 1 object model complete

## FFD 2.0 RC1.0.10 — Multi-page PDF Reproduction QA Pass 1
- Multi-page PDF source pages now use one consistent maximum-fit print geometry.
- Equal A4 pages render at identical size and position; single-page certificate and photo layouts are preserved.
## FFD 2.0 RC1.0.11 — Family-based Book Scope & Lineage Selection
- Added book-specific family scope with paternal-path default selection.
- Added Book Section / Chart Only family selection without changing genealogy data.
- Added bounded incoming-spouse context charts: direct ancestry, siblings, sibling partner/marriage and children, stopping at those children.
- Preserved the existing descendant tree and RC1.0.10 multi-page PDF reproduction contract.


## FFD 2.0 RC1.0.11.1 — Family Scope & Book Presentation QA Pass 1
- Added scoped-publication progress spinner.
- Limited scoped collateral chart expansion to paternal siblings' children.
- Added HTML original-file links for PDF and image media.
- Renamed and restyled spouse family chart and paired it after the main family chart.

## FFD 2.0 RC1.0.11.2 — Unified Family Charts & HTML Book QA Pass 2

- Unified main and spouse family chart presentation.
- Added direct paternal couple ancestry above the husband's parents.
- Enforced spouse collateral stop at sibling children.
- Corrected scoped History Book HTML format submission.
\n## FFD 2.0 RC1.0.11.3 — Dual-Line Family Charts & HTML Parity QA Pass 3\n- Added Husband's Descendants and Wife's Descendants to both embedded family charts.\n- Brought HTML History Book chart content to parity with PDF-source HTML.\n- Recorded standalone all-level Family & Descendants report as a future enhancement.\n
## FFD 2.0 RC1.0.11.3.1 — Spouse Family Chart Root Correction
- Rooted Spouse Family & Descendants on the actual chapter couple rather than the incoming spouse's parents.
- Preserved spouse ancestry and bounded sibling-family context above/around the correct family.
- Applied the shared correction to HTML and PDF History Books.

## FFD 2.0 RC1.0.11.3.2 — Spouse Family-of-Origin Chart Correction
- Reworked Spouse Family & Descendants around the incoming spouse's family of origin.
- Added Father's Paternal Line and Mother's Paternal Line from the spouse's parents.
- Kept the current marriage as Family and replaced the separate sibling block with Wife's Family & Descendants.
- Added restrained rule-based presentation with responsive stacking and no colour dependency.

## FFD 2.0 RC1.0.11.3.3 — Unified Family Chart Presentation
- Presentation-only: Family & Descendants now uses the established Spouse Family & Descendants visual language.
- Family lineage and parent sections stack vertically, row rules are removed, and the central Family is emphasised with section rules.
- Spouse Family & Descendants data and presentation are unchanged.

## FFD 2.0 RC1.0.11.3.3.1 — Spouse Lineage Stacking Correction
- Presentation-only: Father's Paternal Line and Mother's Paternal Line now stack vertically in Spouse Family & Descendants.
- No genealogy, data, traversal, or other chart presentation changes.

## FFD 2.0 RC1.0.12 — Standalone Descendant Report Pass 1
- Added standalone indented Descendant Report generation for 1–6 generations.
- Added HTML and PDF output paths independent of History Book scope.
- Publish UI remains unchanged for Pass 1 while the report presentation is reviewed.

## FFD 2.0 RC1.0.12.1 — Descendant Report Preview Access Correction
- Added a visible Descendant Report — Preview (HTML) control beneath each family on Person > Publish.
- Preview remains fixed at four generations for Pass 1 review.

## FFD 2.0 RC1.0.12.2 — Descendant Report Controls & Presentation QA
- Added a normal Descendant Report configuration page with family selection, 1–6 generations and HTML/PDF output.
- Replaced the misleading Family Report (HTML) Publish control with Descendant Report….
- Added explicit standalone report logo sizing while preserving the accepted report body layout.

## FFD 2.0 RC1.0.12.3 — Publish & Descendant Report UX Cleanup
- Reworked Person > Publish into consistent report tiles and family cards.
- Removed redundant starting-family selection when family context is already known.
- Added a clear 1–6 generation selector and inclusion summary to Descendant Report configuration.
- Kept the accepted report renderer and genealogy unchanged.

## FFD 2.0 RC1.0.12.4 — Publish Report Tile Alignment & Iconography
- Replaced letter badges with report-specific monochrome SVG icons.
- Aligned Descendant Report and Family-history Book controls with the established report-tile layout.
- Added consistent iconography and chevrons to family-level Descendant Report actions.
- Report content remains unchanged for later review.

## FFD 2.0 RC1.0.12.4.1 — Publish Icon Column Alignment Correction
- Standardised the Publish tile icon column and text start position.
- Applied matching icon geometry to family cards.
- Optically centred the existing SVG artwork and lifted the Descendant tree icon slightly.

## FFD 2.0 RC1.0.12.4.2 — Publish Tile DOM Alignment Correction
- Replaced mixed form/link Publish tiles with one shared form > button.publish-action DOM structure for all five actions.
- Preserved GET navigation for Descendant Report and Family-history Book.
- No report generation or genealogy changes.

## FFD 2.0 RC1.0.12.4.3 — Publish Families Duplication Removal
- Removed the redundant Families section from Person > Publish.
- Descendant Report is now the single Publish entry point for descendant reporting.
- Deferred Research Profile, Biography and Person Report presentation harmonisation.

## FFD 2.0 RC1.0.13 — Navigation, Person Focus & Conversation UX Consolidation
- Consolidated left navigation hierarchy, active states and selected-person context.
- Added explicit Current person labeling to the persistent person strip.
- Compacted conversation focus into one bar with explicit Move to and Return to origin actions.
- Relationship/query resolution behaviour is unchanged.

## FFD 2.0 RC1.0.13.0.1 — Person Context Mode-aware QA Correction
- Corrected the RC1.0.13 Current-person QA so it does not incorrectly require the compact person strip on Presentation Overview.
- No UI or application behaviour changes.

## FFD 2.0 RC1.0.13.1 — Persistent Global Navigation, Person Header Parity & Home Explore Removal
- Added persistent Research and Output navigation appropriate to Presentation/Research mode.
- Removed duplicated Explore/Research launch cards from Home.
- Added the person-context header to Family Chart and Ask about.
- Context-search and relationship behaviour are unchanged.

## FFD 2.0 RC1.0.13.1.1 — Reports Person Header Parity
- Reports now inherits the normal person header when opened in person context.
- Removed the redundant Back-to-person button from contextual Reports.
- Global Reports remains person-neutral.
