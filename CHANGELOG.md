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
