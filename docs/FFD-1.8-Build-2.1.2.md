# FFD 1.8 Build 2.1.2 — Default Family Startup & Lifecycle UX

This narrow hardening build completes the Family File lifecycle introduced in Build 2.

## Accepted behaviour

- **Default** is the Family File that opens on the next Companion launch.
- **Active** is the Family File currently being viewed in the running session.
- If the saved default differs from the prior active Family File at launch, Companion safely materialises the default GEDCOM and marks it active without rewriting its stored fingerprint/provenance.
- Delete confirmations describe the actual state transition for the selected Family File rather than using generic active/default wording.
- Three-family regressions cover default, active and ordinary inactive Family Files without requiring deletion of the user's Knuckey dataset.
