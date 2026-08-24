# RC1.0.11 Implementation Handoff

## Build identity

FFD 2.0 RC1.0.11 — Family-based Book Scope & Lineage Selection

## Implementation strategy

Keep the existing descendant-tree implementation intact. Reuse presentation components only where that can be done without changing descendant-tree behaviour.

Introduce a book-specific scope model whose stable identity is a family/couple unit rather than a person. The model should support at least two states:

- `book_section`
- `chart_only`

The default scope is calculated from the paternal path between the selected root and endpoint. All family units on that path become `book_section`; immediate siblings remain represented but their own families remain outside recursive publishing unless explicitly promoted.

Manual overrides must be stored with the report/book configuration, never written back as genealogical attributes.

## Suggested separation of responsibilities

1. **Lineage resolver**
   - Given root person and endpoint person, resolve the paternal chain.
   - Convert each parent/child step into the relevant family/couple unit.
   - Fail clearly if no paternal path exists rather than silently choosing a different lineage.

2. **Book-scope model**
   - Maintain selected family IDs/keys.
   - Apply defaults from lineage resolver.
   - Apply explicit user promotions/demotions.
   - Expose deterministic ordered families for publishing.

3. **Publishing traversal**
   - Replace unrestricted descendant recursion with traversal constrained by selected family units.
   - Immediate children remain visible in the current family.
   - Only a child whose own family is selected produces another full family chapter.

4. **Family selector UI**
   - Present the surrounding family structure using the established descendant-tree visual language where practical.
   - Clearly distinguish `Book Section` from `Chart Only`.
   - Changing scope must not mutate underlying genealogy.

5. **Spouse context chart**
   - Generated separately from recursive book scope.
   - May include direct spouse ancestry as available.
   - May include spouse siblings, their partner/marriage, and their children.
   - Stop at sibling children.
   - Never convert any of this contextual material into selected book families.

6. **Endpoint handling**
   - The final selected family is allowed to terminate naturally.
   - Do not require selection of another child merely to continue a paternal rule.

## Regression protections

- Existing descendant tree output and interaction must remain unchanged.
- Existing History Book media/PDF reproduction behaviour from RC1.0.10 must remain intact.
- Book selection must not mutate people/families/events in the companion database.
- Existing reports not using the new selector should either retain legacy behaviour intentionally or receive a deterministic migration/default. Do not silently mix both behaviours.

## Implementation caution

Do not encode “paternal” as a permanent characteristic of a book family. Paternal traversal is only the automatic default-selection algorithm. The underlying scope mechanism must remain generic enough for manual additions and future alternate-root books.

Do not recursively traverse spouse contextual families. Treat the spouse chart as a bounded read-only view built from relationship data.
