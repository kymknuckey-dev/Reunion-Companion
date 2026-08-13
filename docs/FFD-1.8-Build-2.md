# FFD 1.8 Build 2 — Portable Mac Installation, Environment Bootstrap & Family File Foundation

Baseline: Git commit `25fde92`, tag `ffd-1.8-build-1.1.2b`.

## Delivered

- Family File registry with immutable workspace UUIDs, display names, source application, GEDCOM path, default/active state and structural GEDCOM fingerprints.
- Existing installations migrate automatically to a default **Knuckey Family History** Family File without rebuilding the genealogy data.
- Home title comes from the active Family File.
- Data Manager exposes Family Files and **Add Family File**.
- Persistent Family File selector in the running web UI.
- Selecting a Family File safely materialises that Family File's remembered GEDCOM through the existing staged refresh mechanism. The genealogy query engine therefore continues to operate against one isolated active dataset at a time while all Family File identities/configuration live in the same Companion SQLite database.
- Wrong-GEDCOM protection: refresh compares the incoming GEDCOM against the active Family File fingerprint. A likely different family is blocked and the user is directed to Add Family instead.
- Source application metadata is independent of GEDCOM format, so non-Reunion GEDCOM sources can be registered.
- Portable-Mac preflight/bootstrap for Apple Silicon, Python, Git, Ollama and `gemma3:4b`.
- Persistent local LLM configuration at `~/.reunion-companion/config.json`; environment variables still override it.

## Deliberate boundaries

Build 2 does not claim universal interpretation of vendor-specific GEDCOM extensions. Standard GEDCOM continues through the existing importer; Reunion custom tags already supported by Companion remain supported. Unknown vendor extensions remain a future compatibility enhancement.

Family File switching requires the remembered GEDCOM file to be accessible on that Mac. This is intentional: Reunion/GEDCOM remains authoritative and Companion does not silently merge genealogy datasets.
