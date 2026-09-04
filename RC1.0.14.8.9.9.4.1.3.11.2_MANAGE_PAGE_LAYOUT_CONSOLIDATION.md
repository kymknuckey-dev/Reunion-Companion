# FFD 2.0 RC1.0.14.8.9.9.4.1.3.11.2 — Manage Page Layout Consolidation

## Scope
Reorganises the existing Data Manager without changing its underlying data-management behaviour.

## Layout
- Family Files is a compact family-management section with the active/default Family File prominent and secondary Add/Rename controls revealed only when needed.
- Reunion GEDCOM consolidates current GEDCOM identity, dataset counts, current refresh, new-export refresh, last-refresh status and Import History.
- Import History remains paginated at ten rows per page, but is collapsed beneath the GEDCOM section by default.
- Ryerson Crawler is visually separated as an external-research service and retains crawler state, controls, detailed status counts and recent activity.
- Refresh feedback is displayed as a compact status banner.

## Behaviour preserved
- Family File rename/default/delete/add actions and report deletion lifecycle.
- Safe staged current-GEDCOM refresh and safe refresh from a new GEDCOM.
- Import-history pagination.
- Ryerson start/pause control and status semantics.
- Three most recent persisted crawler activities.

## QA
Targeted Manage/Family File/Ryerson/packaging regression set: 19 passed before compatibility alignment; all Manage-related historical regressions pass after alignment.
Full snapshot suite: 1275 passed, 1 failed. The sole failure is the pre-existing `test_shared_hash_pager_controls_are_not_collapsed` Ryerson pagination-control regression and reproduces unchanged against the supplied pre-patch source snapshot.
