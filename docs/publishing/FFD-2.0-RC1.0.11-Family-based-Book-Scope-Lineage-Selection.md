# FFD 2.0 RC1.0.11 — Family-based Book Scope & Lineage Selection

RC1.0.11 changes the History Book from unrestricted descendant recursion to a book-specific family selection model.

## Delivered behaviour

- A History Book can be configured from a starting person to an endpoint on the recorded paternal line.
- Companion resolves the paternal path from explicit recorded father/family roles rather than surname or sex inference.
- Families on that path default to **Book Section**.
- Other descendant families remain **Chart Only** until explicitly selected.
- The selector allows additional family units to be promoted into the book without recursively selecting their branches.
- Immediate siblings remain present in the family context of their parents.
- Incoming spouses receive a separate chart-only context showing available direct ancestry plus sibling families.
- Spouse siblings may show partner/marriage and children; traversal stops at those children.
- Spouse context never creates extra narrative book chapters.
- The existing descendant chart remains a separate feature and is not rewritten by this build.

## Compatibility boundary

Existing low-level/CLI calls that do not provide book scope retain legacy descendant traversal. The application History Book workflow now directs the user through the scope selector before publication.
