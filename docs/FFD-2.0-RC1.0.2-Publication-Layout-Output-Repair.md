# FFD 2.0 RC1.0.2 — Publication Layout & Output Repair

Baseline: FFD 2.0 RC1.0.1  
Genealogy engine: FFD 1.9 RC1

## Image pagination
- Landscape photographs are full-width publication items, stacked vertically.
- No more than two landscape photographs are grouped into a PDF page unit.
- Image, caption and source text remain an atomic non-breaking unit.
- Portrait photographs normally occupy one page unit and are capped at 202 mm image height so caption/source text has reserved page space.
- HTML uses the same vertical grouping; screen output simply ignores physical page breaks.

## Family & Descendants typography
A common publication hierarchy is applied:
- person name: normal text size, bold;
- life dates: 84% text size, normal weight, visually secondary;
- Children and Family & Descendants use the same hierarchy;
- Husband/Wife and descendant lines are normalised at publication rendering without changing genealogy relationships or dates.

## PDF-only publishing
When only PDF is requested, HTML and asset files are generated in a temporary working directory. WeasyPrint consumes them there and the temporary HTML/assets are deleted automatically. Only the requested PDF remains in the report directory.

Explicit HTML publishing remains unchanged and retains its HTML/assets.
