# FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.10.3.4.1 — Native Finder Tag Metadata QA Correction

This QA correction supersedes the stale Finder-tag regression contracts left in an overlaid development repository by RC1.0.14.8.9.9.4.1.3.12.10.3.1–.3.

The accepted native macOS contract is based on Finder-generated metadata observed on the target Mac:

- Red named tag: `Reunion - Not Referenced\n1`
- FinderInfo label bits: `0x0002` for red
- `/usr/bin/xattr` is used in the frozen runtime
- Removal preserves unrelated named tags and recalculates/clears FinderInfo colour bits.

No production reconciliation behaviour changes from .12.10.3.4; this release corrects the persisted regression tests so full installer verification reflects the native Finder contract.
