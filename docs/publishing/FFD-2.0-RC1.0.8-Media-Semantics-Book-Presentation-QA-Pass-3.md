# FFD 2.0 RC1.0.8 — Media Semantics & Book Presentation QA Pass 3

## Purpose

Freeze the verified Reunion media semantics and book presentation behaviour after live-data diagnostics.

## Accepted behaviour

- Reunion `_PRIM Y` is imported as `media.is_preferred = 1`.
- Person hero/portrait selection prefers `is_preferred = 1`; media order is only the fallback.
- Other photographs are paginated two per A4 book page, stacked vertically.
- Portrait and landscape photographs preserve their complete aspect ratio with `object-fit: contain`; publication does not crop them into landscape frames.
- Family `MARR -> OBJE` media survives import as `family-event / Marriage` and remains linked through `family_media`.
- Marriage and wedding certificates attached beneath the Reunion marriage event are surfaced as marriage documents.
- Image figures do not provide an open-original link.
- GEDCOM import and Safe Refresh semantics established in Pass 2 are frozen; Pass 3 is a publishing acceptance/hardening pass.

## Live diagnostic evidence used for acceptance

- Kym Wayne Knuckey: `Knuckey, Kym Wayne at 2.jpeg` is the preferred person photograph.
- Mervyn Neil Knuckey / Elaine Fay Cox: marriage certificate is present as family-event Marriage media.
- Kym Wayne Knuckey / Susan Lee Jones: marriage certificate is present as family-event Marriage media.
