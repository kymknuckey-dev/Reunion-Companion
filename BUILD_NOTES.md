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
