# FFD 2.0 RC1 — Release Candidate Stabilisation

Baseline: FFD 2.0 Build 6.0.2 — Backend Ownership Hardening  
Genealogy engine: FFD 1.9 RC1

## RC1 changes

### Search
Person search now treats entered words as name components. `Kym Knuckey` can match `Kym Wayne Knuckey` while preserving broader one-word searches and ambiguity handling.

### Published person layout
- Person sections begin with the person's name and portrait, when available.
- The duplicated vital-fact block beneath the name is removed.
- `Life & Notes` is deterministic factual material grouped into `Life Events`, `Education`, and `Work Life`.
- Individual life-event concepts such as Birth, Christening, Religion and Residence render on separate lines.
- `Publication Narrative` is renamed `Biography`.

### Canonical Biography
The stored in-app Biography is now canonical. It remains unchanged until the user explicitly chooses **Regenerate Biography**. Publishing reads that same stored Biography and does not independently invoke the LLM, so app, HTML and PDF use identical Biography prose.

The Biography prompt now explicitly introduces the subject by full name and then uses the given/first name naturally. Courtesy-title forms such as `Mr. Knuckey` are prohibited unless historically significant evidence requires them.

### Family & Descendants
- `Family Context & Descendants` becomes `Family & Descendants`.
- Husband and wife each display their own life dates.
- Descendant spouses keep dates attached to the correct individual.

### Photographs
`Other Photographs` uses a two-column publication grid with bounded image height, making more economical use of PDF pages while preserving aspect ratios.

### Sources
Reader-facing numbered citations use `[n]`. Fact citations come from their event-source links. Media citations are associated through shared event/family attachment context, allowing labels such as `Marriage Certificate [12]` without inventing source relationships. The consolidated Sources section remains in the publication.

## Preserved from Build 6.0.2
- self-contained runtime;
- DMG packaging;
- first-run workflow;
- Reunion Files security-scoped bookmark;
- backend ownership validation;
- rejection of incompatible/foreign port-8765 services;
- FFD 1.9 RC1 genealogy-engine baseline.
