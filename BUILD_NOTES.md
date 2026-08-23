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
