# FFD 2.0 RC1.0.3 — Birth Document Fitted Page Structural Repair

This replaces the prior Birth Documents CSS/page-break approach with an independent first-page renderer.

## Required print structure

The first PDF in Birth Documents is no longer passed through the ordinary archive-page renderer. `_birth_document_block()` produces one dedicated A4 publication page containing:

- Birth Documents section heading
- document title and source reference
- first PDF page preview, scaled to the remaining printable area
- document caption/source text
- Open original PDF link

Only source-PDF pages 2 and later use the normal `.archive-page` renderer.

This removes the competing page breaks that previously produced a heading-only page followed by a certificate page.

## HTML

HTML retains the normal Birth Documents heading and natural first-page PDF preview/link. The dedicated fitted page is print-only.

## Scope

No changes are made to accepted landscape-photo layout, portrait media layout, descendant typography, biography reuse, sources, backend ownership, or PDF-only temporary HTML cleanup.
