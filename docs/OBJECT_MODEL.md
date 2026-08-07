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


## v0.6 canonical API

```python
from reunion_companion.domain import load_reunion_database

db = load_reunion_database("/path/to/family.familyfile14")
person = db.get_person(1)

print(person.display_name)
print(db.summary())
print(db.find_events(event_type="birth"))
```

`GenealogyTree`, `PersonProfile`, and `FamilyUnit` remain compatibility aliases.
New code should use `ReunionDatabase`, `Person`, and `Family`.
