# Object Model

The object model is deliberately independent of Reunion's binary layout.

## Initial entities

- Person
- Family
- Event
- Place
- Note
- Media
- Source
- Citation
- Repository

A parser may initially leave unknown values as `None` while retaining raw offsets and identifiers for later decoding.

## Semantic layer

`GenealogyTree` resolves Reunion record IDs into reusable `PersonProfile` and `FamilyUnit` objects for publishing, search, and future AI features.
