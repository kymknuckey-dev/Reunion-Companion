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
