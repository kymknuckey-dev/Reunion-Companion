# FFD 1.9 Build 1.1 — Publication Visual Refinement & Activity Feedback

This refinement keeps the accepted FFD 1.9 Build 1 narrative/content behaviour and improves the publication experience for both HTML and print-ready PDF.

## Changes

- Publication person summaries and image figures no longer use card-style borders/boxes.
- Landscape photographs may use the available publication width while preserving aspect ratio.
- Small landscape originals are not forced to full width and unnecessarily enlarged.
- Portrait photographs are constrained to a consistent maximum height and centred.
- Square/intermediate photographs receive a moderate centred size.
- Primary person portraits are deliberately smaller than documentary/story photographs.
- Images are never cropped by the publication rules (`object-fit: contain`).
- Long-running publication now shows an animated activity indicator with the real classes of work involved: preparing family information, writing publication narrative, and rendering the document/media.
- No artificial percentage is displayed because local-LLM and document-rendering time is variable.
- Release identity is updated to FFD 1.9 Build 1.1.

## Design rule

Presentation remains an application UI. Publication should read and look like a book, so publication templates favour typography, whitespace and restrained separators over web-style cards.
