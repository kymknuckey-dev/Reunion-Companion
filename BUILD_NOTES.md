# Foundation Layer v0.10.0-alpha4

## Milestone

Alpha 4 is the first release that converts the verified v0.9 semantic database
into the new Foundation object graph.

## Added

- `FoundationBuilder`
- `FoundationBuildReport`
- semantic-model adapter
- `from_semantic_database(...)`
- `from_package(...)` convenience adapter
- package/version/warnings metadata in `FoundationDatabase`
- deterministic Foundation-local event IDs
- person/family relationship linking
- person/family event attachment
- semantic place resolution
- unresolved place-text preservation
- source offsets and decoder status carried into Foundation events
- seven new tests

## Architectural boundary

Alpha 4 does **not** decode Reunion binary data itself. `from_package()` first
uses the established v0.9 `load_reunion_database()` path and then adapts that
verified semantic model into Foundation objects.

No existing application path is changed.
