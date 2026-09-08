# FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.10.3.4 — Native Finder Tag Metadata Correction

This QA correction aligns Companion's `Reunion - Not Referenced` Finder tag with metadata observed from Finder itself on the target Mac. Finder's standard Red tag is stored as a user-tag string ending in `\n1`, and FinderInfo mirrors the colour in the label bits (`0x0002`). Companion now writes/removes both representations together while preserving unrelated tags and FinderInfo bits.
