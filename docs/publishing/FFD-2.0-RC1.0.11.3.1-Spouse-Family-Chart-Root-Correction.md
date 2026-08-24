# FFD 2.0 RC1.0.11.3.1 — Spouse Family Chart Root Correction

## Purpose

Correct the semantic root of **Spouse Family & Descendants** in both HTML and PDF History Books.

## Rule

The central **Family** must always be the actual married couple represented by the current book chapter.

The incoming spouse's parents and direct ancestry belong above that couple as ancestry/context. They must never replace the chapter couple as the Family.

The descendants below the Family belong to the actual married couple.

Existing bounded spouse-family context remains:
- spouse siblings may be shown;
- their partner/marriage may be shown;
- their children may be shown;
- traversal stops at those children;
- none of those contextual families become book chapters.

Because HTML and PDF use the same History Book HTML source, the root correction applies to both outputs.

## Example

Correct central Family:
- Victor Alexander Knuckey
- Lois Aletha Waight

Context above Lois:
- Albert William Waight
- Eva Alice Manners

Albert and Eva must not become the central Family in the Spouse Family & Descendants chart.
