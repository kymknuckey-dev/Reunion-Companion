# Roadmap

## v0.1 — Foundation

- Package detection
- Main data file detection
- Read-only binary access
- Packed-date decoder
- Initial person model
- Probe regression tests

## v0.2 — Core records

- Person IDs and names
- Sex
- Person events
- Families and children
- Places and place usage

## v0.3 — Research data

- Notes
- Media
- Sources
- Citations
- Repositories

## v0.4 — Export and validation

- JSON
- CSV
- Markdown
- Missing-data checks
- Broken-media checks

## Later

- Search
- Reusable family-history publishing
- PDF and DOCX output
- Optional AI assistant


## 0.7 relationship engine

Implemented:

- parent/child/spouse graph
- ancestor and descendant traversal
- shortest path
- sibling and cousin naming
- nearest common ancestors
- disconnected components

Future relationship work:

- half and step relationships
- adoption and foster relationship roles
- multiple parent sets
- lineage selection
- relationship phrasing sensitive to sex and role


## 0.8 event engine

Implemented:

- generic semantic event registry
- person and family event occurrences
- chronological sorting with partial dates
- event search and filtering
- personal timelines
- source-coverage audit
- decoder-status catalogue
- plug-in person-event decoder registry

Controlled probes still required for binary decoding of:

- Death
- Burial and Cremation
- Baptism and Christening
- Occupation and Residence
- Census
- Immigration and Emigration
- Military Service
- Education and Probate
- Divorce
- Custom events
