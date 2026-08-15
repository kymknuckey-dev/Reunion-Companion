# FFD 1.9 RC1 — Consolidation Release Candidate

FFD 1.9 RC1 freezes the proven genealogy functionality before Reunion Companion moves into the FFD 2.0 applicationisation phase.

## Scope

RC1 introduces no new genealogy capability and makes no Biography synthesis changes. It preserves:

- Build 3 Presentation/Research Timeline and Sources separation.
- Build 4.0.1 deterministic immediate-family grounding in Biography.
- Existing GEDCOM refresh, publishing, database, local-LLM and diagnostic/CLI behaviour.

## Golden live Biography behaviours

These are release acceptance behaviours, validated against the real Reunion data rather than encoded as synthetic personal data fixtures.

- Victor: marriage to Lois is naturally represented; Mervyn and Brian are both children; no son/grandson corruption; no unnecessary marriage repetition.
- Elaine: Mervyn, marriage date/place, and Kym/Jodie/Jamie are represented as the recorded immediate family.
- Mervyn: Elaine, marriage, and Kym/Jodie/Jamie are represented; an independent narrative mention of Jamie does not cause him to disappear from the complete family statement.

## RC1 acceptance

1. Full automated test suite passes.
2. Golden Biography live checks pass.
3. Presentation Timeline and Sources behaviour remains correct.
4. Research Timeline and Sources behaviour remains correct.
5. Publishing smoke test passes.
6. GEDCOM refresh smoke test passes.
7. Working tree is clean before tagging `ffd-1.9-rc1`.

Once accepted, FFD 1.9 is feature-frozen except for genuine RC defects. New product/application work moves to FFD 2.0.
