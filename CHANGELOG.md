# Changelog

## 0.7.0-dev1 — Relationship Engine

- Added ancestor and descendant traversal by generation.
- Added shortest decoded relationship paths through parent, child, and spouse links.
- Added sibling, ancestor, descendant, cousin, and removed-cousin labels.
- Added nearest common-ancestor reporting.
- Added disconnected relationship-component detection.
- Added `relationship`, `ancestors`, `descendants`, and `components` commands.


## 0.6.0-dev1 — Semantic Foundation

- Added the permanent `reunion_companion.model` package.
- Added canonical ReunionDatabase, Person, Family, Event, Place, Source, Citation, Media, and Note objects.
- Added Evidence metadata for decoded, inferred, experimental, and unresolved values.
- Refactored publishing and question answering to use the semantic model.
- Preserved historical domain/model imports and all existing CLI commands.
- Added the `database` semantic-summary command.


## 0.5.0-dev1

- Added the first grounded question-answering engine.
- Added deterministic natural-language intents for relationships, Birth facts, sources, place searches, and data-quality checks.
- Added evidence-rich text and JSON answers.
- Added the `ask` command.


## 0.4.0-dev1

- Added the first publishing layer.
- Added reusable Markdown person profiles.
- Added `profile --output` file generation.
- Added profile JSON output for future DOCX/PDF renderers.


## 0.3.0-dev1

- Added free-form master source extraction.
- Added event-specific citation detail extraction.
- Joined citation Source IDs to master source titles.
- Added citations to semantic Event JSON and person output.
- Added the `sources` command.


## 0.2.0-dev6

- Added controlled media Description and Comment extraction.
- Linked Probe-20 metadata to MaryProbePortrait.jpg.
- Added media metadata to person profiles and JSON output.
- Added an explicit metadata evidence-status field.


## 0.2.0-dev5

- Added controlled multi-media filename/path mapping.
- Verified Person 1 and Person 2 media ownership from thumbnail names.
- Mapped ProbePortrait.jpg to Test Probe and MaryProbePortrait.jpg to Mary Probe.
- Retained an explicit evidence status for ordered media mapping.


## 0.2.0-dev4

- Added media and thumbnail extraction.
- Decoded thumbnail owner type, owner ID, fingerprint, and size.
- Linked controlled single-media filename and original path.
- Added media to person profiles and semantic JSON.
- Added the `media` command.


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
