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
