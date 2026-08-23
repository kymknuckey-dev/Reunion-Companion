# FFD 2.0 RC1.0.10 — Multi-page PDF Reproduction QA Pass 1

## Consistent Maximum-Fit Document Pages

Multi-page PDFs are reproduced with one identical print geometry for every source page.
A4 is the normal source-page target, while arbitrary PDF page sizes remain supported through
aspect-ratio-preserving `object-fit: contain` rendering.

Acceptance requirements:
- every source page is rendered in source order;
- equal-sized pages in one PDF receive identical print geometry;
- the source page uses the maximum practical A4 printable area;
- no cropping, stretching, or aspect-ratio distortion;
- compact, fixed document furniture cannot change source-page scale;
- single-page Birth/Marriage certificate presentation remains unchanged;
- RC1.0.9 photograph layout remains unchanged.
