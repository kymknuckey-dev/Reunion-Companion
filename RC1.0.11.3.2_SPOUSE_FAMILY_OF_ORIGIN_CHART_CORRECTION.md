# FFD 2.0 RC1.0.11.3.2 — Spouse Family-of-Origin Chart Correction

## Agreed genealogy model

Spouse Family & Descendants presents the incoming spouse's family of origin while preserving the current chapter marriage as the connection point.

1. **Father's Paternal Line** — direct paternal ancestry of the spouse's father.
2. **Mother's Paternal Line** — direct paternal ancestry of the spouse's mother.
3. **Wife's Parents** — the spouse's birth-family parents.
4. **Family** — the current married couple remains unchanged.
5. **Wife's Family & Descendants** — the wife's parents' children, each child's spouse/family, and their children. Traversal stops there.

The spouse's siblings are therefore not a separate context block: they are naturally represented as children of the Wife's Parents in Wife's Family & Descendants.

## Presentation

- Reuse the established Family & Descendants typography, spacing and simple section rules.
- Do not depend on colour.
- Do not draw a rule beneath every person row.
- Emphasise the central Family with stronger section rules.
- Father's and Mother's paternal lines may sit side by side when space permits.
- Stack those lines vertically when width is constrained rather than compressing genealogical content.
- HTML and PDF use the same chart source.

## Scope boundary

This remains bounded book context. It does not recursively expand the spouse's collateral descendants beyond the children of the Wife's Parents' children.
