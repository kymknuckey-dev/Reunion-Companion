## FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.9.2 — Event Media Publication Context Correction

- History Book publication now treats Reunion event attachment context as authoritative.
- Birth event media is grouped with Birth Documents; Death, Burial and Cremation event media is grouped with Death & Burial Documents.
- Filename/title/folder heuristics remain only as fallback classification.
- Regression covers Brian Victor Knuckey-style Burial photos with generic titles.


## FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.9.1 — Data Quality Event & Era Drilldown
- Data Quality primary lists now drill down by event/fact type before showing records.
- Event/fact types drill down again by rolling era: last 100 years, 100–200 years, more than 200 years, or unknown context.
- Existing Actionable / Review / Low opportunity classifications remain visible only at the record-list level for evaluation.
- Era boundaries roll with the current year rather than using fixed calendar dates.

## FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.9 — Actionable Data Quality Centre

- Replaces the overwhelming Unsourced events / facts quality card with Missing information and Present but unsourced.
- Separates Marriage quality through family records and retains missing Death events in Priorities.
- Adds transparent first-pass actionability: 1900+ Actionable, 1800s Review, pre-1800 Low opportunity.
- Preserves Place variants, Missing media, Legacy PICT, Untitled sources and Duplicate source titles.
- Retains the RC1.0.14.8.9.9.4.1.3.12.8.2.1 Ryerson national-coverage queue correction.
- Restores executable permission for scripts/reunion-ryerson in the release package.

## FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.8.2.1 — Ryerson National Coverage Queue Correction QA Fix
- Installer QA compatibility correction: superseded .12.8.1 targeted-queue regression now reflects the .12.8.2 architecture.
- Ryerson State reset now explicitly sets selectedIndex=0 as well as selecting the national/All States option.

Ryerson national coverage bookkeeping corrected to the normal person crawler; historical SA-limited successes are safely requeued without deleting findings or review decisions. The family-wide paused queue is restored.


### RC1.0.14.8.9.9.4.1.3.8 CORRECTED-4
- Restored the historical HTML/PDF shared-source call shape when `Paternal path last` is not requested.
- Keeps the new ordering preference additive while preserving the earlier spouse-chart regression contract.
## FFD 2.0 RC1.0.14.8.9.9.4.1.3.5 — Waiting-for-Reunion Reconciliation Hardening

- Re-evaluates every accepted Waiting for Reunion discovery against the current imported Reunion state on refresh.
- Accepted evidence with no proposed Reunion fact no longer remains permanently waiting; it completes on reconciliation because no Reunion change is required.
- Adds regression coverage for later acceptance after the fact already exists in Reunion and publication-only evidence.

## FFD 2.0 RC1.0.14.8.9.9.4.1.2 — External Evidence Review Handoff Restoration
- Fix: Ryerson Death research findings now appear in External Evidence Review as soon as they are stored.
- Fix: existing stored findings are backfilled when the normal crawler starts, restoring people missed while the handoff was absent.

## FFD 2.0 RC1.0.14.8.9.9.4.1.1 — Ryerson CLI Control Alignment
- Aligned `./scripts/reunion-ryerson start|pause|status|recent` with the active Death research crawler used by Manage.
- Normal CLI start/pause now keep the older Family-wide crawler explicitly paused.
- `status` reports Death research as the primary crawler and shows Family-wide separately as dormant state.
- `recent` now reads recent Death research activity instead of the Family-wide targeted queue.
- Added explicit inspection-only `family-status`, `family-recent`, and `family-populate` commands for the retained legacy queue.
- Focused CLI and release-metadata regression: 11 passed.

## FFD 2.0 RC1.0.14.8.9.9.4.1 — Ryerson Explicit No-Result & Restart Recovery Correction
- Fixed genuine Ryerson zero-result pages being misclassified as `Waiting · Ryerson search did not complete; retry later`.
- Added automatic recovery for interrupted Ryerson queue state after an application restart.
- No matching, genealogy, database schema, or Family-wide crawler scope changes.

## FFD 2.0 RC1.0.14.8.9.9.4 — Ryerson Timeout Overload Retry Hardening

- Hardened Safari-backed Ryerson retrieval so overloaded searches that never leave the populated search form are preserved for retry.
- Added a final timeout snapshot and transient-page classification before recording a terminal Safari result timeout.
- No schema, matching, crawler-scope, or family-wide queue changes.

## FFD 2.0 RC1.0.14.8.9.9.3 — Targeted Ryerson Crawler Control Correction

- Corrected Ryerson crawler control so broad family-wide surname harvesting no longer restarts with normal crawler operation.
- Family-wide crawling is forced paused at app startup without deleting or rewriting its existing queue or discoveries.
- Normal crawler operation is now limited to surname + first-given-name death research.

## FFD 2.0 RC1.0.14.8.9.9.2 — Ryerson First-Given-Name Search Consolidation

- Consolidated the legacy/death-research Ryerson retrieval path to one surname + first-given-name query.
- Removed the former full-given-names request followed by first-name fallback, avoiding a potential extra Safari/Ryerson search for people with multiple given names.
- Preserved surname-only searching where no given name is recorded.
- Full given names remain available to downstream candidate matching and evidence assessment; targeted crawler behaviour, queue state, matching, database, and UI are unchanged.

## FFD 2.0 RC1.0.14.8.9.9.1 — External Evidence Review Presentation Consolidation

- Recast External Evidence Review as a compact person-level review index rather than a second candidate decision workspace.
- Review-state results now show one concise row per person with candidate count and Reunion context; opening the person continues to the full Person > Research evidence view.
- Removed candidate-level decision controls and raw candidate detail from the review index.
- Removed the redundant “Research Priorities” return link.
- Styled review-state navigation as Companion controls and hid “No Longer Eligible” from the normal review-state bar while retaining the underlying state and records.
- Preserved Most Recent / Relationship ordering, relationship anchoring, pagination, crawler, matching, decision-state, database, and Reunion write-back behaviour.

## FFD 2.0 RC1.0.14.8.9.9 — Person Research Workflow Consolidation

- Consolidated Person > Research around automated External Evidence review by removing the legacy manual Search Ryerson card.
- Kept the underlying manual import/parser path intact while removing its redundant user-facing entry point.
- Research evidence flags now use the same "Needs evidence" warning treatment as Person Overview.

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

## FFD 2.0 RC1.0.14.8.9.9.4.1.3 — External Evidence Confidence-First Recent Review
- External Evidence Review `Most Recent` now prioritises the strongest person-level candidate confidence first.
- 100% matches appear before 75% matches; within each confidence tier, newest candidate event date remains first.
- Relationship sorting is unchanged.

## RC1.0.14.8.9.9.4.1.3.1 — External Evidence Review Confidence Propagation Correction
- Persist Ryerson match confidence into the discovery review index.
- Re-materialise stored Ryerson evidence once at app startup so existing review rows receive their confidence without altering review decisions.
- Most Recent now prioritises confidence recorded on the actual review candidates, with existing external-evidence lookup retained only as a fallback.

### FFD 2.0 RC1.0.14.8.9.9.4.1.3.2
- External Evidence Review now ranks a person from the highest confidence of any currently unresolved candidate, preventing a live 100%/95% match from being held down by a stale lower-confidence review-index value.
- Regression coverage locks Previous navigation on page 2 for Next People to Review, Research Needed, Data Quality, and the full External Evidence Review workspace.


## FFD 2.0 RC1.0.14.8.9.9.4.1.3.3 — Candidate Confidence Ordering & Single Pager Placement
- External Evidence Candidate cards now sort by confidence descending first, then event-date recency within the same confidence.
- The date-order toggle preserves confidence as the primary sort key.
- Research and External Evidence pagination is shown once at the bottom of each paginated section; Previous/Next behaviour is unchanged.
## FFD 2.0 RC1.0.14.8.9.9.4.1.3.4 — Relationship Answer Synthesis Regression Correction
- Relationship searches with an internal marriage link now synthesise a concise by-marriage explanation instead of exposing the raw parent/child/spouse graph path.
- Choosing a person from a duplicate-name relationship ambiguity now resolves that selected identity for the relationship question instead of redisplaying the same ambiguity.
- Regression coverage locks both behaviours while preserving existing blood-relationship, focus, pronoun and possessive relationship contracts.

### RC1.0.14.8.9.9.4.1.3.4 corrected QA overlay
- Restores the established direct spouse-of-child relationship wording before the generic internal-marriage synthesis path.
- Prevents a short `child -> spouse` relationship from being widened into the generic “related by marriage through …” answer.
- Keeps the new internal-marriage synthesis and duplicate-name identity-resolution fixes intact.


## FFD 2.0 RC1.0.14.8.9.9.4.1.3.6 — Funeral Notice Death-Fact Reconciliation Correction
- Correct Ryerson funeral notices so their publication/event date is not materialised as a second Reunion death date.
- Historical waiting funeral-notice rows created with a legacy death-date key now reconcile as evidence-only and can complete after GEDCOM refresh.

## FFD 2.0 RC1.0.14.8.9.9.4.1.3.7 — Persistent Report Configurations

- Added persistent, named Report Configurations without changing report generation.
- Family-history Book configurations can retain the paternal endpoint, selected family expansions, and preferred output format.
- Descendant Report configurations can retain the starting family, generation depth, and preferred output format.
- Multiple configurations of the same report type are supported and distinguished by name.
- Configurations are stored in the Companion database, survive application restarts and GEDCOM refreshes, and can be loaded, updated, saved as new, or deleted independently.
- Existing PDF/HTML creation buttons and publishing renderers are unchanged; with no saved configuration loaded, publishing follows the existing RC1.0.14.8.9.9.4.1.3.6 behaviour.

## FFD 2.0 RC1.0.14.8.9.9.4.1.3.8 — Hierarchical Family Chapter Selection & Ordering
- Added progressive, expandable family-branch selection to Family-history Book scope.
- Any descendant family can be independently promoted to a chapter; expanding a branch does not select it.
- Chapter order is now family-grouped breadth-first so siblings and families of the same generation stay together before deeper branches.
- Existing report configurations continue to persist the exact selected family IDs.
- No changes to chapter rendering, HTML/PDF engines, media handling, or report content.
- CORRECTED: fixed misleading leaf indentation (for example Jamie appearing visually beneath Kym), restored true parent-family nesting, ordered sibling families oldest-first from recorded Birth events, and made chapter traversal parent + immediate child families before deeper descendants.

- RC1.0.14.8.9.9.4.1.3.8 refinement: added a saved **Paternal path last** family-history ordering option. Within each sibling-family group, selected side families print first and the recorded paternal continuation prints last before the report moves deeper.

### FFD 2.0 RC1.0.14.8.9.9.4.1.3.8 CORRECTED-5
- Corrected Family History chapter order to birth-order, branch-first traversal.
- Paternal path is now used to construct/default the scope, not to override reader-facing sibling order.
- Removed the `Paternal path last` Publish option while retaining compatibility with older call signatures/configuration data.

## FFD 2.0 RC1.0.14.8.9.9.4.1.3.8 CORRECTED-6 — Family-level-first chapter ordering
- Corrected Family History publication traversal so all selected sibling family chapters are emitted together in recorded child birth order before descending into the next generation.
- Preserves the original/early family grouping near the front of the book while retaining natural birth-order reading within later generations.
- Selector hierarchy and saved report configuration behaviour are unchanged.


### FFD 2.0 RC1.0.14.8.9.9.4.1.3.8 CORRECTED-7 — Configurable branch-order changeover
- Added one optional Family History setting, **Branch ordering starts here**.
- Above the selected family, historical sibling-family levels remain grouped in birth order.
- From the selected family downward, each selected child's branch is completed in birth order before the next sibling branch begins.
- `None` preserves the CORRECTED-6 family-level ordering throughout.
- The changeover family is persisted in named Report Configurations and applies identically to HTML and PDF.
- No family selector hierarchy, report content, chart, media, or rendering behaviour was otherwise changed.

### FFD 2.0 RC1.0.14.8.9.9.4.1.3.8 CORRECTED-8
- Family History HTML/PDF page-economy presentation pass: removed duplicate Children section/page break and gently tightened body/heading typography while retaining existing A4 margins.

### FFD 2.0 RC1.0.14.8.9.9.4.1.3.8 CORRECTED-8B — Consolidated Source Index
- Removed the repeated `Sources Used in This Chapter` section and its forced page break from Family History chapters.
- Retained inline source references and the existing end-of-book Source Index unchanged.
- No source data, family ordering, report configuration, typography, chart, media, or rendering semantics changed.

### FFD 2.0 RC1.0.14.8.9.9.4.1.3.8 CORRECTED-8C — Biography Source Consolidation
- Removed repeated person-level Sources lists beneath Family History biographies.
- Source records remain collected in the consolidated end-of-book Source Index.
- No changes to biography text, citations/evidence storage, family ordering, media, or charts.

### FFD 2.0 RC1.0.14.8.9.9.4.1.3.8 CORRECTED-8C-A — Biography Sources Regression Test Alignment
- Corrected an obsolete historical regression assertion that still required the deliberately removed Biography Sources block.
- Preserves the consolidated end-of-book Source Index requirement.
- No production behaviour changes from CORRECTED-8C.


### FFD 2.0 RC1.0.14.8.9.9.4.1.3.11.2 — Manage Page Layout Consolidation
- Reorganised Data Manager into compact Family Files, Reunion GEDCOM, and Ryerson Crawler sections.
- Consolidated current/new GEDCOM refresh controls and dataset statistics into one Reunion GEDCOM panel.
- Moved paginated Import History beneath the GEDCOM section and collapsed it by default while preserving all history and paging.
- Reduced persistent Family File form clutter by revealing Add/Rename controls only when needed.
- Preserved existing Family File, safe refresh, Ryerson crawler, and recent activity behaviour.

## FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.2 — Ryerson Retry Timing Visibility
- Added the actual next eligible Death Research retry time to Manage > Ryerson Crawler.
- Retry timing is derived from persisted retry queue state and the source-wide cooldown; the later gate wins.
- Shows local clock time plus relative wait when a retry is pending, otherwise `Next retry: None pending`.
- Recent crawler activity remains reserved for completed/past activity.


## FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.6.1 — Research Value Specificity Correction
- Tightened Research Value to account for candidate-set ambiguity and recency.
- Recent missing-Death leads are High only when the current candidate set is specific (one or two candidates).
- Broad common-name result sets are downgraded to Needs careful review instead of appearing as High opportunity.
- Older (>100 year) missing-Death leads are downgraded from High opportunity.
- Exact normalized agreement with an existing unsourced Reunion Death remains the strongest High opportunity signal.


## FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.6.2 — Discovery Match Grading
- Replaced the experimental Research Value sort with visual Discovery Match Grading.
- Retained Most Recent and Relationship as the two review orderings.
- Grades current new Ryerson candidates as Strong match, Supported match, Possible match, Low specificity, or Unassessed.
- Birth-date agreement is the strongest deterministic identity signal; place and family-detail corroboration provide supporting evidence.
- Candidate count expresses ambiguity but does not override one individually strong birth-date match.
- Shows publication title as review context without treating the newspaper alone as proof of identity.

## FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.6.4 — Grouped Review & Birth Match Correction
- Group discoveries visually by match grade while retaining Most Recent and Relationship ordering within each group.
- Place pagination controls inside each collapsible grade group.

## FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.6.5 — Review-State Match Grading Correction

- Apply discovery match grading to candidates in the currently viewed review state, not only `new` discoveries.
- Confirmed Complete, Waiting for Reunion, Deferred, Already Known and Rejected views retain Strong/Supported/Possible/Low Specificity grading when linked Ryerson identity evidence is available.
- Preserve New review grouping behaviour unchanged.

## FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.6.6 — External Evidence Identity & Review Lifecycle Correction
- Makes external source-record identity independent of proposed_fact_key so parser reinterpretation cannot resurrect completed evidence as New.
- Consolidates historical review rows for the same person/source/external record while preserving the strongest reviewed lifecycle state.
- Consolidates historical exact external-evidence duplicates and repoints review state to the canonical evidence record.
- Prevents recurrence through the common remember_discovery and add_external_evidence boundaries.
- Preserves Discovery Match Grading across review states.
