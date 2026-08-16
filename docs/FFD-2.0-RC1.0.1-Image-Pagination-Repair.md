# FFD 2.0 RC1.0.1 — Image Pagination Repair

Baseline: FFD 2.0 RC1  
Engine: FFD 1.9 RC1

This repair removes the free-flow two-column photograph grid introduced in RC1.

## Publication rule
PDF pagination drives photograph layout:
- landscape photographs are grouped into explicit publication units of no more than two photographs;
- a landscape pair is sized with room for captions and source references and is kept together as one PDF page unit;
- portrait photographs normally form a single-photo page unit;
- aspect ratios are preserved;
- HTML uses the same landscape-pair and single-photo units, with print-only page breaks disabled on screen.

All successful RC1 search, Biography, Life Events, descendants and source changes are retained.
