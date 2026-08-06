# Reunion Companion

Reunion Companion is a read-only companion application for Reunion genealogy software.

Its long-term purpose is to provide:

- safe extraction of people, families, events, places, notes, media, and sources
- structured JSON and CSV export
- data validation and research assistance
- reusable family-history publishing
- optional AI-assisted querying and narrative generation

## Core principle

**Reunion Companion must never modify a Reunion family file.**

The original Reunion package is opened read-only and converted into an independent internal object model.

## Current status

Early parser foundation for Reunion 14 probe files.

## Development setup

```bash
cd "$HOME/Development/Reunion Companion"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the tests:

```bash
pytest
```

Run the command-line program:

```bash
reunion-companion --help
```

Inspect a Reunion package:

```bash
reunion-companion inspect "/path/to/My Family.familyfile14"
```

## Architecture

```text
Reunion family file
        ↓
BinaryReader
        ↓
Decoder
        ↓
Object model
        ↓
Export / Publishing / Search / AI
```

## Decode cache contents

```bash
reunion-companion inventory "/path/to/My Family.familyfile14" --cache-values
```

The index values are currently labelled as **slots**, not definitive visible-person totals, because deleted and reserved record behaviour is still under investigation.


## Structured tree extraction

```bash
reunion-companion tree "/path/to/Probe-16.familyfile14"
reunion-companion tree "/path/to/Probe-16.familyfile14" --raw-fields
reunion-companion tree "/path/to/Probe-16.familyfile14" --json
```

The current family output distinguishes directly decoded child-family references
from spouse relationships inferred from the controlled one-family probe pattern.


### Current event extraction

The `tree` command now includes controlled-probe Birth and Marriage dates,
the known `abt` qualifier, the Birth memo, and directly decoded spouse IDs.
Event places remain unlinked until place-usage pointers are decoded.


## Semantic object model

```bash
reunion-companion person "/path/to/file.familyfile14" --id 1
reunion-companion person "/path/to/file.familyfile14" --name "Probe"
reunion-companion family "/path/to/file.familyfile14" --id 1
```


### Event places

Birth and Marriage event place tokens are now resolved through `places.cache`,
so semantic person and family output includes named locations.


### Person notes

General person notes are now included in `person`, `tree`, and JSON output.


## Media extraction

```bash
reunion-companion media "/path/to/file.familyfile14"
reunion-companion media "/path/to/file.familyfile14" --json
```

Thumbnail filenames provide direct person/family ownership, a media fingerprint,
and generated size. Original filename/path linking is proven for the controlled
single-media probe; multi-media mapping remains a later probe.


### Multiple media items

Probe-19 confirms ordered multi-media mapping for two person images. Thumbnail
ownership is direct (`p1`, `p2`); filename and original-path records map in the
same stable order. The decoder reports this as
`decoded-ordered-controlled-probes`.


### Media description and comment

Probe-20 decodes Mary Probe's media Description and Comment. The description is
stored in her person-media block; the comment is stored in a separate metadata
area. The current link is labelled
`decoded-single-metadata-controlled-probe` pending a second metadata test.


## Sources and citations

```bash
reunion-companion sources "/path/to/file.familyfile14"
reunion-companion person "/path/to/file.familyfile14" --id 1
```

Probe-21 establishes a master free-form Source record and an event-specific
Birth citation that references the Source ID and stores citation detail.


## Person profile publishing

Print a Markdown profile:

```bash
reunion-companion profile "/path/to/file.familyfile14" --id 1
```

Write it to a file:

```bash
reunion-companion profile "/path/to/file.familyfile14"   --id 1   --output "Test Probe.md"
```

The profile combines relationships, events, places, memos, notes, media, and
sources from the semantic model.
