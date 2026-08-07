# Architecture

Reunion Companion is divided into four layers.

## 1. Binary reader

Reads bytes and package contents without interpreting genealogy semantics.

## 2. Decoder

Converts known binary structures into typed intermediate records.

## 3. Object model

Represents people, families, events, places, notes, media, and sources independently of Reunion's storage format.

## 4. Consumers

Exports, publishing, validation, search, and AI features consume the object model.

## Safety boundary

No component writes to a Reunion family file.


## v0.6 semantic boundary

The permanent public model lives under `reunion_companion.model`.

```text
Reunion package
    ↓
binary/cache decoders
    ↓
ReunionDatabase
    ├── Person
    ├── Family
    ├── Event
    ├── Place
    ├── Source / Citation
    ├── Media
    └── Note
         ↓
publisher / query / validation / future GUI
```

Code outside the decoder and package-reader layers consumes semantic objects,
not Reunion binary tags or offsets.


## Event engine boundary

Binary event decoders return the same semantic `Event` object. The
`EventEngine` then provides indexing, timelines, filtering and coverage
analysis without knowing any Reunion field tags.

```text
Reunion person/family record
        ↓
registered event decoder
        ↓
Event
        ↓
EventOccurrence
        ↓
timeline / search / publisher / ask / validation
```
