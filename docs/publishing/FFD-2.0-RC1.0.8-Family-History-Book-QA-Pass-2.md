# FFD 2.0 RC1.0.8 — Family History Book QA Pass 2

## Scope

- Preserve accepted Birth, Death/Burial and Other Document fitted-page publishing.
- Discover Marriage/Wedding Certificate media using both Reunion title and original filename, including image certificates.
- Make book publishing validate biography cache evidence/version and regenerate stale pre-hardening biographies, preventing GEDCOM CHAN/Changed metadata prose from surviving in publication.
- Make publishing itself ensure a biography exists; prior Biography-page visitation is not required.
- Replace the separate Individual Overview / Life & Notes structure with the Dad-derived person publication hierarchy:
  - Life & Biography
  - Person name
  - Birth Date, Birth Place
  - Occupation, Education, Religion
  - Father, Mother
  - Spouse, Marriage Date, Marriage Place
  - Children
  - portrait at right using the person's preferred publication/hero portrait when available
  - Biography
  - Sources
- Multiple values remain grouped under their single label.
- No large portrait void is reserved when a person has no portrait.
- Incoming Spouse Family Context remains deferred.
