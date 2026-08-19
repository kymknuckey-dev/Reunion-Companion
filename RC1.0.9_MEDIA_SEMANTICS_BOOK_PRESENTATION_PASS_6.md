# FFD 2.0 RC1.0.9 — Media Semantics & Book Presentation Pass 6

This cumulative build is based directly on the supplied RC1.0.8 QA Pass 6 corrected package.

## Accepted behaviour retained
- Reunion preferred person photo drives the hero portrait.
- Marriage certificates attached beneath family marriage events are imported and published.
- Other photographs are paginated two per page.
- Portrait/square photographs use a 106 mm maximum image height in paired pages.
- Landscape photographs retain the accepted 91 mm maximum image height.
- All paired photographs use `object-fit: contain`; no cropping is permitted.

## Pass 6 correction
- Each photograph/caption card now spans the full printable width and centres its contents within that width, preventing the right-shift seen in RC1.0.8 output.
- Existing image size allowances are unchanged.
- Original-file links and clickable PDF preview wrappers are removed from publication output.

## Regression result
`762 passed`
