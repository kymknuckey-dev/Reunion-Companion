# Reunion Companion Foundation Layer — Alpha 4

This is the first Foundation release that can represent real Reunion genealogy
data.

Data flow:

```text
.familyfile14
    ↓
verified v0.9 decoder
    ↓
verified v0.9 semantic ReunionDatabase
    ↓
FoundationBuilder
    ↓
FoundationDatabase
```

The old model remains authoritative for the application. Alpha 4 is a parallel,
read-only representation so the new Core Engine can be validated safely before
any migration begins.
