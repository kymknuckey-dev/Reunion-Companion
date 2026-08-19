# FFD 2.0 RC1.0.8 — Media Semantics & Book Presentation QA Pass 6

## Scope

Pass 6 returns to the known-good Pass 4 baseline and changes only the `Other Photographs` book layout.

## Changes

- Replaces the implicit flex layout with two explicit image-plus-caption slots per page.
- Each slot is 113 mm high: up to 106 mm for the image and a reserved 7 mm caption row.
- Portrait and square photographs may use the larger 106 mm image area.
- Landscape photographs retain the accepted Pass 4 maximum height of 91 mm.
- All photographs remain `object-fit: contain`; cropping is prohibited.
- Caption overflow is visible rather than clipped by the image slot.
- Preferred-photo and family-event certificate behaviour from Pass 4 is unchanged.

## Regression

756 tests passed.
