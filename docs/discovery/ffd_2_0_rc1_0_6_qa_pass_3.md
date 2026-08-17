# FFD 2.0 RC1.0.6 — Search & Identity Discovery, QA Pass 3

## Purpose

QA Pass 3 replaces score-only ambiguity presentation with explicit identity-result lanes. It does not broaden search scope.

## Result lanes

1. **Best likely matches** — strong, explainable spouse-surname identity interpretations, including combined conservative given-name variation plus spouse-surname association.
2. **People recorded with this name** — authoritative Reunion name matches and direct given-name variants.
3. **Other family/name associations** — weaker but still explainable association candidates.

A result appearing in Best likely matches does not alter the person's Reunion name and does not assert that a spouse surname was adopted.

## Natural-language questions

Person-anchored questions from Search use the same identity lanes before selection. Requested-fact availability remains separate from identity confidence and cannot manufacture residence, marriage, or other facts.

## Build identity

The macOS About and Diagnostics strings now derive from the single `APP_RELEASE` and `ENGINE_BASELINE` definitions in `macos_app/build_app.py`, preventing stale release labels in generated launchers.

## Acceptance focus

Real-family QA should repeat:

- Susan Jones
- Susan Knuckey
- Sue Knuckey
- Where did Susan Knuckey live?
- Who did Susan Knuckey marry?

The first screen should now be materially different: strong explained association candidates are visible in Best likely matches before large populations of literal historical duplicates, while recorded Reunion identities remain clearly separated and authoritative.
