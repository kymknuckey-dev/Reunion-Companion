# FFD 2.0 RC1.0.8 — Media Semantics & Book Presentation QA Pass 1

## Purpose

Align Reunion Companion media import and publication behaviour with Reunion's media semantics and the accepted Family History Book presentation rules.

## Implemented

- Import media nested beneath a family Marriage event (`FAM -> MARR -> OBJE -> FILE`) and preserve it as family marriage media.
- Preserve Reunion `_PRIM Y/N` media preference in the Companion media model.
- Prefer `_PRIM Y` images for person hero/thumbnail/publication portrait selection, falling back deterministically when no preferred image is supplied.
- Publish Other Photographs in two vertically stacked best-fit slots per page regardless of portrait/landscape orientation.
- Preserve image aspect ratio with `object-fit: contain`; do not crop merely to fill a slot.
- Keep the final odd photograph to a sensible half-page-scale slot rather than enlarging it to a full-page image.
- Preserve Family History Book QA Pass 3 marriage-document behaviour and all accepted Life & Biography work.

## Regression coverage

Regression tests cover Reunion family Marriage-event media, `_PRIM Y` preferred-photo selection, and two-slot vertical book photo pagination.
