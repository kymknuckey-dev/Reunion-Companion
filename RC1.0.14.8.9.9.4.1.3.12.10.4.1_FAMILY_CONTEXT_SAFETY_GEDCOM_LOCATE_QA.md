# FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.10.4.1 — Family Context Safety & GEDCOM Locate QA

- Family File switching pauses the Ryerson crawler before materialising the incoming GEDCOM.
- Family File switching skips External Evidence eligibility reconciliation, preventing another family's valid discoveries being retired.
- The normal Ryerson queue is bound to the Family File that starts it; runner ticks refuse a mismatched active Family File.
- Manage shows Queue Family File and a family-change pause notice.
- Locate GEDCOM uses explicit .ged/.gedcom extension filtering for native macOS selection.
- Expected GEDCOM, status/Locate and Safe Refresh are grouped before statistics.
- No automatic data repair is performed: the verified 840-row incident recovery remains preserved in the user's repaired database.
