# Foundation Layer v0.10.0-alpha5

## Added

- `FoundationNote`
- `FoundationMedia`
- `FoundationSource`
- `FoundationCitation`
- note attachment to people/families
- media attachment to people/families
- source repository and source-title index
- citation repository and event/source/owner links
- media filename index
- expanded Foundation build report
- six new content tests

## Design

Notes, media, and citations do not currently have stable Reunion object IDs in
the verified semantic model. Alpha 5 therefore assigns deterministic,
Foundation-local integer IDs while preserving original offsets/keys in fields
and metadata.

## Safety

The build remains one-way and read-only:

```text
.familyfile14
    ↓
verified v0.9 decoder
    ↓
verified semantic model
    ↓
FoundationBuilder
    ↓
FoundationDatabase
```

No established application module is replaced.
