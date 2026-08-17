# FFD 2.0 RC1.0.6 — Search & Identity Discovery, QA Pass 4

## Purpose

QA Pass 4 removes the entry-point divergence discovered during real-family testing. Search the Family and Ask about the Family now use the same explicit-name identity discovery candidate pool and the same result-lane policy.

## Behaviour

- An explicit person name in a question overrides conversational proximity for identity discovery.
- Current conversation focus remains sticky until the user explicitly selects or moves focus.
- Duplicate recorded names no longer cause Ask to discard credible spouse-surname or given-name association candidates.
- Ask uses the same first-screen lanes as Search: Best likely matches, People recorded with this name, and Other family/name associations.
- First-screen limits and More… disclosure behaviour are aligned between entry points.
- Question-relevant-data hints remain ranking/presentation aids only and never fabricate evidence.
- The authoritative Reunion person name is never rewritten by an inferred association.

## Acceptance cases

The candidate set and grouping for each explicit-name question must be equivalent when entered from Search the Family or Ask about the Family, including:

- `Where did Susan Knuckey live?`
- `Who did Susan Knuckey marry?`

Susan Lee Jones must remain discoverable through the recorded relationship to Kym Wayne Knuckey in both entry points, without asserting that Reunion records her as Susan Knuckey.

## Build identity

About and Diagnostics derive from the authoritative application release constant and identify this build as QA Pass 4.
