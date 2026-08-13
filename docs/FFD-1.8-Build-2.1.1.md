# FFD 1.8 Build 2.1.1 — Family Identity & Lifecycle Hardening

Corrective build for the Family File foundation introduced in FFD 1.8 Build 2 / 2.1.

## Behaviour

- Switching Family Files materialises the selected GEDCOM without rewriting the Family File fingerprint, source provenance, or Family File import history.
- Both `Safe Refresh Current GEDCOM` and `Safe Refresh from New GEDCOM` run the same Family File identity preflight.
- A likely wrong-family GEDCOM is rejected before staging/promotion and the existing data is retained.
- The mismatch screen includes a real **Add as a New Family File** form carrying the selected GEDCOM path forward.
- Default and active are lifecycle state, not deletion locks.
- Any Family File may be deleted when another Family File survives.
- Deleting the active Family File safely materialises a surviving Family File first.
- Deleting the default Family File promotes a surviving Family File to default.
- The only remaining Family File cannot be deleted.
- Optional generated-report/assets deletion remains explicit.

## Acceptance sequence

1. Use Knuckey and Hewitt Family Files with overlapping GEDCOM IDs.
2. Switch repeatedly between them and change the default Family File.
3. Confirm a Hewitt GEDCOM cannot refresh the active Knuckey Family File.
4. Confirm the mismatch page offers **Add as a New Family File**.
5. Delete Hewitt while Knuckey is default, then repeat with the opposite default arrangement.
6. Confirm the surviving Family File becomes active/default as required and its genealogy is materialised.
