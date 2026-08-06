# Changelog

## 0.2.0-dev3

- Decoded standalone general person-note records.
- Added semantic Note objects and person-profile note output.
- Preserved UTF-8 text and paragraph line breaks.


## 0.2.0-dev2

- Decoded length-prefixed event place tokens (`[[pt:n]]`).
- Decoded stable place IDs from `places.cache`.
- Resolved Birth and Marriage events to named places.
- Added place IDs to semantic event JSON.


## 0.2.0-dev1

- Added semantic genealogy object model.
- Resolved parents, spouses, and children.
- Added person and family commands.
- Added semantic JSON output.

## 0.1.0-dev4

- Decoded full packed calendar years while retaining unknown high flags.
- Added known `abt` date qualifier decoding.
- Added person birth-event extraction, including the controlled birth memo.
- Decoded direct spouse IDs from family fields 0x0050 and 0x0051.
- Added family marriage-date extraction.
- Added event data to text and JSON tree output.


## 0.1.0-dev3

- Added structured Reunion 14 person-record envelope decoding.
- Added decoded record IDs and sex codes.
- Added experimental child-to-family references.
- Added provisional family graph output with explicit inference labels.
- Added the `tree` command and JSON output.


## 0.1.0-dev2

- Decoded Reunion 14 given-name and place offset-table caches.
- Added conservative surname extraction from `surnames.cache`.
- Added index slot counts and trailing ID reporting.
- Added place-usage count reporting.
- Added `inventory --cache-values`.

## 0.1.0-dev1

- Created initial project structure.
- Added read-only package inspection.
- Added initial packed-date decoder.
- Added foundational object models.
