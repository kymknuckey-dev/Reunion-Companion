# FFD 2.0 RC1.0.10 — Multi-page PDF Reproduction

## Purpose

Family History publishing must reproduce every page of every PDF media item that reaches the book, regardless of whether Reunion attached that media to a person, an event such as Birth, a family, or a family event such as Marriage.

## Publishing contract

- A PDF remains one logical media item in Companion.
- The renderer determines the actual PDF page count from the source file.
- Every source page is rendered in original order.
- Page 1 retains the established fitted-document treatment for the section in which the document appears.
- Pages 2+ continue immediately as dedicated archive pages.
- Every rendered page preserves the source aspect ratio and uses `object-fit: contain`; cropping is prohibited.
- Portrait and landscape PDF pages retain the existing fitted orientation rules.
- Single-page Birth and Marriage certificates remain visually unchanged.
- The approved RC1.0.9 photograph-page layout is frozen and must not change.
- GEDCOM/media attachment semantics are not rewritten by publishing.

## Real-world acceptance set

The intended Reunion/Companion cases are:

1. `Knuckey, Mervyn Neil 1933-09-24 Birth Certificate.pdf` — one-page event/Birth PDF.
2. `The memories of Mervyn Neil Knuckey.pdf` — two-page direct person PDF. Both pages must appear consecutively in the book.
3. `Knuckey, Mervyn Neil & Cox, Elaine Fay 1961-01-21 Marriage Certificate.pdf` — one-page family-event/Marriage PDF.

The multi-page rule is attachment-scope independent.
