# FFD 2.0 RC1.0.3 — Atomic Media & Descendant Typography Repair

Baseline: FFD 2.0 RC1.0.2  
Genealogy engine: FFD 1.9 RC1

## Portrait and wedding media
The Mervyn Neil Knuckey publication exposed the remaining failure precisely: a portrait-format wedding photograph could occupy one page while its `Open original image` link was pushed onto the next. RC1.0.3 treats the figure, caption, citation and original-file link as one non-breaking media object and limits portrait/square image height in print so related text has reserved space.

The accepted two-landscape, vertically stacked page treatment is retained unchanged.

## Family & Descendants
Person typography is now emitted semantically by the descendant renderer rather than inferred afterwards with regular expressions. Every person can therefore render as:
- **name** — normal body size and bold;
- **dates** — smaller (84%) and normal weight.

This applies to parents, Husband/Wife, Children and descendant spouses, fixing the case where the wife's name inherited date styling.

## Automated publication isolation
The publication report directory supports a controlled `REUNION_COMPANION_REPORT_DIR` override. The Foundation shell publishing test uses pytest temporary storage, preventing the three Charles Henry James Knuckey / Elizabeth Anne Hunter test publications from appearing in the user's real Reports directory.

Normal Companion publishing is unchanged when the override is absent.

## Retained RC behaviour
Search, canonical Biography reuse, Life Events, numbered sources, PDF-only temporary HTML/assets cleanup, backend ownership and Reunion Files access are unchanged.
