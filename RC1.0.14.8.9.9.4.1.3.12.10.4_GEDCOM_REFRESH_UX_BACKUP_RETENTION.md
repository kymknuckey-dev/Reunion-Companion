# FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.10.4 — GEDCOM Refresh UX & Backup Retention

## Scope

- Make Safe Refresh GEDCOM the single normal refresh action for the active Family File.
- Show the exact expected GEDCOM filename and full path, plus found/missing status.
- Remove the permanently visible Choose Different GEDCOM path field/button.
- When the expected GEDCOM is missing, expose a contextual Locate GEDCOM… action backed by the native macOS file picker.
- Retain only the latest 3 automatic Safe Refresh database backups after a successful verified refresh.
- Add Manage visibility for recovery-backup count, size and retention policy.
- Add explicit Clean Up Old Backups action for the existing accumulated backlog.
- Cleanup removes surplus automatic refresh backups, stale reunion-companion-refresh staging files, and the obsolete companion.sqlite3.before-bickle-cleanup checkpoint.
- The deliberate companion-before-ryerson-reset.sqlite3 checkpoint is never touched.

## Safety

Automatic pruning occurs only after a successful verified GEDCOM refresh and promotion. Failed refreshes do not prune recovery backups.
