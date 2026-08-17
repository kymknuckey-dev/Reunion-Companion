# FFD 2.0 RC1.0.6 — Search & Identity Discovery, QA Pass 2

This pass refines identity ranking without expanding Search & Identity Discovery scope.

## Changes

- Literal recorded display names outrank given-name variants, even when Reunion component fields contain a formal given name.
- Direct recorded-name matches remain stronger than inferred family/name associations.
- Combined given-name-variant plus spouse-surname associations remain prominent among association candidates.
- Low-information placeholder-style display names are conservatively de-emphasised for recognition only; Reunion identity is never rewritten.
- Question evidence ranks candidates only when the requested fact is actually recorded. Absence of Residence data does not infer residence.
- Ambiguity presentation continues to separate direct names from people who may be known by that name through family associations.

## Real-family acceptance cases

- Susan Jones
- Susan Knuckey
- Sue Knuckey
- Where did Susan Knuckey live?
- Who did Susan Knuckey marry?

Susan Lee Jones must remain Susan Lee Jones in all results. Any Knuckey match through Kym Wayne Knuckey is an explained search association, not a claim that her recorded surname changed.
