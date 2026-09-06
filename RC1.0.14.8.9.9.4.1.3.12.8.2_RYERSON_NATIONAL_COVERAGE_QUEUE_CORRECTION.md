# FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.8.2 — Ryerson National Coverage Queue Correction

- Keeps every live Ryerson search national by explicitly selecting the all-state option.
- Moves national-coverage bookkeeping to the authoritative normal person crawler (`companion_external_scan_queue`).
- Requeues historical successful SA-limited person scans once while preserving external evidence and review decisions.
- Preserves successful national scans performed after the .12.8.1 all-state correction.
- Marks every newly successful normal-crawler scan with `coverage_scope=national` and a completion timestamp.
- Restores the paused family-wide targeted queue that .12.8.1 mistakenly rewound.
