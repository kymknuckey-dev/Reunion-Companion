# FFD 2.0 RC1.0.8 — Media Semantics & Book Presentation QA Pass 4

## Scope

Narrow publishing-only correction for portrait photograph pagination. The proven GEDCOM media importer, preferred-photo semantics, and event-attached marriage certificate handling are unchanged.

## Change

Photo-pair print pages now override the legacy single-photo 198 mm print rule. Each photograph in a two-slot page is constrained to the 91 mm image area inside its 108 mm vertical slot, with width and height automatic and `object-fit: contain`. This prevents portrait photographs from overflowing the slot and being clipped into a landscape-shaped viewport.

## Acceptance

- Two portrait photographs may appear vertically on one page.
- Each portrait remains complete and keeps its original aspect ratio.
- No cropping to fill the page width.
- Landscape and square photographs use the same best-fit slot behaviour.
- Preferred hero-photo and marriage-certificate behaviour from Pass 3 remains unchanged.
