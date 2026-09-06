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
- Restored the live handoff from successful Ryerson Death research findings into External Evidence Review.
- Starting the normal Ryerson crawler now backfills already-stored Ryerson findings into the review index without rerunning source searches.
- New findings are materialised immediately after a successful crawler scan.
- Existing review decisions remain idempotent/preserved; Family-wide crawler behaviour is unchanged.

## FFD 2.0 RC1.0.14.8.9.9.4.1.1 — Ryerson CLI Control Alignment
- Aligned `./scripts/reunion-ryerson start|pause|status|recent` with the active Death research crawler used by Manage.
- Normal CLI start/pause now keep the older Family-wide crawler explicitly paused.
- `status` reports Death research as the primary crawler and shows Family-wide separately as dormant state.
- `recent` now reads recent Death research activity instead of the Family-wide targeted queue.
- Added explicit inspection-only `family-status`, `family-recent`, and `family-populate` commands for the retained legacy queue.
- Focused CLI and release-metadata regression: 11 passed.

## FFD 2.0 RC1.0.14.8.9.9.4.1 — Ryerson Explicit No-Result & Restart Recovery Correction
- Recognises Ryerson's explicit `0 notices found` / `No results found` response as a successful completed search instead of transient overload.
- Requeues interrupted `searching` rows on app startup and when the normal crawler is started; expired `retry_wait` rows are also made runnable.
- Preserves Family-wide surname crawler dormancy and existing queue/findings data.
- Focused regression: explicit no-result transport, timeout overload handling, and restart recovery.

## FFD 2.0 RC1.0.14.8.9.9.4 — Ryerson Timeout Overload Retry Hardening

- Reclassifies a Ryerson Safari result timeout as transient when the final page is an explicit overload response or remains on the submitted search form.
- Transient result timeouts now enter Waiting/retry handling rather than exhausting into the permanent Failed bucket.
- Retains genuine Safari/transport failures as failures and leaves queue/database schema unchanged.
- Adds focused regression coverage for explicit overload, pending-form timeout, and unrelated-page timeout semantics.

## FFD 2.0 RC1.0.14.8.9.9.3 — Targeted Ryerson Crawler Control Correction

- Normal Ryerson Start/Pause now controls only the surname + first-given-name death-research crawler.
- The older family-wide surname crawler is explicitly paused on application startup and whenever the normal Ryerson control is used.
- Existing family-wide queue state, completed work, failures and discoveries are preserved; no database cleanup or migration is performed.
- Manage continues to display the family-wide counts as historical/dormant status while crawler state is driven only by death research.
- Legacy internal family-wide routes and machinery remain available for regression/history, but are no longer started by the normal user-facing control.

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

- Removed the obsolete person-level manual Search Ryerson / paste-result workflow now superseded by automated crawler discovery and External Evidence Candidates.
- Retained the underlying Ryerson copied-result import/parser machinery for compatibility and regression coverage.
- Aligned deterministic evidence flags with the Overview "Needs evidence" warning badge language and colour treatment.
- No crawler, matching, retry, External Evidence decision, Reunion-writeback, or database behaviour changes.

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

## FFD 2.0 RC1.0.14.8.9.9.4.1.3 — External Evidence Confidence-First Recent Review
- External Evidence Review `Most Recent` now prioritises the strongest person-level candidate confidence first.
- 100% matches appear before 75% matches; within each confidence tier, newest candidate event date remains first.
- Relationship sorting is unchanged.

## RC1.0.14.8.9.9.4.1.3.1 — External Evidence Review Confidence Propagation Correction
- Persist Ryerson match confidence into the discovery review index.
- Re-materialise stored Ryerson evidence once at app startup so existing review rows receive their confidence without altering review decisions.
- Most Recent now prioritises confidence recorded on the actual review candidates, with existing external-evidence lookup retained only as a fallback.

## FFD 2.0 RC1.0.14.8.9.9.4.1.3.2 — External Evidence Unresolved Confidence Priority & Bidirectional Research Pagination
- Person priority is based on the strongest currently unresolved candidate, with newest candidate event date used within equal confidence.
- Bidirectional pagination is regression-locked across all Research review lists and the full External Evidence Review workspace.


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
- Regression target: Graham Robert Shearer pattern where death 05JUN2015 is already confirmed and funeral notice 11JUN2015 was stranded as `death:11JUN2015`.
- New funeral notices produce no proposed Reunion death fact unless an explicit death date is supplied.
- Legacy waiting rows linked to funeral/publication evidence resolve as evidence-only during refresh reconciliation.

## FFD 2.0 RC1.0.14.8.9.9.4.1.3.7 — Persistent Report Configurations

- Added persistent, named Report Configurations without changing report generation.
- Family-history Book configurations can retain the paternal endpoint, selected family expansions, and preferred output format.
- Descendant Report configurations can retain the starting family, generation depth, and preferred output format.
- Multiple configurations of the same report type are supported and distinguished by name.
- Configurations are stored in the Companion database, survive application restarts and GEDCOM refreshes, and can be loaded, updated, saved as new, or deleted independently.
- Existing PDF/HTML creation buttons and publishing renderers are unchanged; with no saved configuration loaded, publishing follows the existing RC1.0.14.8.9.9.4.1.3.6 behaviour.

## FFD 2.0 RC1.0.14.8.9.9.4.1.3.8 — Hierarchical Family Chapter Selection & Ordering
- Built from accepted .3.7 full-source baseline.
- Publishing change is limited to Family-history scope discovery/selection and selected-family ordering.
- The paternal path remains the default checked route. Side branches are progressively expandable and never auto-selected.
- Candidate traversal has a defensive depth ceiling of 64 family generations.
- CORRECTED QA: sibling family rows are now ordered by the child's recorded Birth date rather than database id, leaf rows align with expandable siblings, and publication ordering emits all selected child families before descending into grandchildren.

### RC1.0.14.8.9.9.4.1.3.8 refinement — Paternal path last
- Added an optional, configuration-persisted ordering rule for Family History reports.
- When enabled, side-family chapters at each sibling level are emitted before the family that continues the paternal path.
- HTML and PDF share the same ordered scope; family selection/rendering content is otherwise unchanged.

### RC1.0.14.8.9.9.4.1.3.8 CORRECTED-5 — Birth-order branch-first chapter ordering
- Kept the accepted expandable family selector unchanged.
- Paternal lineage remains the construction/default-selection spine only.
- Published chapters now follow each family's children in recorded birth order and complete each selected child branch before moving to the next sibling.
- Removed the reader-facing `Paternal path last` option; historical function arguments remain tolerated for compatibility but no longer alter chapter order.

## FFD 2.0 RC1.0.14.8.9.9.4.1.3.8 CORRECTED-6 — Family-level-first chapter ordering
- Corrected Family History publication traversal so all selected sibling family chapters are emitted together in recorded child birth order before descending into the next generation.
- Preserves the original/early family grouping near the front of the book while retaining natural birth-order reading within later generations.
- Selector hierarchy and saved report configuration behaviour are unchanged.


### FFD 2.0 RC1.0.14.8.9.9.4.1.3.8 CORRECTED-7
Publication-order refinement only. Family History configurations can nominate a single family where ordering changes from historical family-level grouping to descendant branch-by-branch birth order. This is deliberately one changeover point only; no automatic heuristic or general chapter designer was introduced.

### FFD 2.0 RC1.0.14.8.9.9.4.1.3.8 CORRECTED-8 — Family History Page Economy QA
- Removed the duplicate standalone Children section and its forced page break from Family History chapters.
- Tightened Family History book typography only: body 10pt/1.36 line-height, H1 22pt, H2 14pt, H3 11pt, with modestly reduced heading spacing.
- Preserved A4 page margins and the existing smaller facts, captions, chapter kickers and page-number styling.
- No family selection, chapter ordering, report configuration, chart, media, or content semantics changed.

### FFD 2.0 RC1.0.14.8.9.9.4.1.3.8 CORRECTED-8B — Consolidated Source Index
- Removed the repeated `Sources Used in This Chapter` section and its forced page break from Family History chapters.
- Retained inline source references and the existing end-of-book Source Index unchanged.
- No source data, family ordering, report configuration, typography, chart, media, or rendering semantics changed.

### CORRECTED-8C — Biography Source Consolidation
Family History person biographies no longer render a repeated Sources block. Source collection remains unchanged for the final Source Index.

### CORRECTED-8C-A — Biography Sources Regression Test Alignment
- Updated the historical Family History QA test to reflect the intentional removal of per-biography Sources blocks.
- The test now requires the per-biography `<h3>Sources</h3>` block to be absent while retaining the final `<h1>Source Index</h1>`.
- No production publishing code changed from CORRECTED-8C.


## FFD 2.0 RC1.0.14.8.9.9.4.1.3.11.2 — Manage Page Layout Consolidation
- Compact three-part Data Manager hierarchy: Family Files, Reunion GEDCOM, Ryerson Crawler.
- Import History nested/collapsed within Reunion GEDCOM; paging retained.
- Add/Rename Family File controls are progressive disclosure rather than permanent form rows.
- Full supplied-source regression run: 1275 passed; one unrelated pre-existing Ryerson hash-pagination test failure reproduced on baseline.

## FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.2 — Ryerson Retry Timing Visibility
- Added the actual next eligible Death Research retry time to Manage > Ryerson Crawler.
- Retry timing is derived from persisted retry queue state and the source-wide cooldown; the later gate wins.
- Shows local clock time plus relative wait when a retry is pending, otherwise `Next retry: None pending`.
- Recent crawler activity remains reserved for completed/past activity.



### FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.6.2 — Discovery Match Grading
External Evidence Review now visually grades identity-match strength while preserving the established Most Recent and Relationship navigation modes. Existing matcher reasons are reused; no AI/fuzzy interpretation is introduced.

### FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.6.4 — Grouped Review & Birth Match Correction
- Rolled External Evidence Review into collapsible match-quality groups.
- Preserved newest-to-oldest ordering inside each group in Most Recent mode.
- Moved Previous/Next navigation inside the group being paged.

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

## FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.7 — Home Recent & Bookmarked Navigation
- Restores Recently Explored People to Home as the primary quick-return navigation aid.
- Places Recently Explored People left of Bookmarked People in a responsive two-column Home layout.
- Records six distinct recently opened people, newest first; revisiting a person moves them to the top without duplication.
- Uses active-Family-File + GEDCOM xref identity so recents survive Safe Refresh GEDCOM replacements and do not leak across family files.
- Preserves existing Bookmarked People behaviour and lifespan identity context.
