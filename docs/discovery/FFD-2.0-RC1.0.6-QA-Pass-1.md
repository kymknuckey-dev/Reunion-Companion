# FFD 2.0 RC1.0.6 — Search & Identity Discovery, QA Pass 1

This pass refines the RC1.0.6 identity-discovery experience without expanding its scope.

## Behavioural refinements

- Exact/direct recorded-name matches remain stronger than inferred family/name associations.
- Question relevance improves ordering within an identity class but does not override identity strength.
- At the no-focus Search entry point, large sets of exact duplicate names no longer hide credible marriage/name-associated candidates.
- Ambiguous results are separated into **Recorded or direct name matches** and **Other possible people through family/name associations**.
- Search shows a manageable first set of direct matches while keeping associated candidates visible.
- Candidate cards include Reunion-grounded recognition context such as spouse and parents when available.
- Inferred surname/name usage remains explanatory only; Reunion's recorded identity is never rewritten.
- Existing question-aware ambiguity behaviour and ordinary person search remain regression-protected.

## Acceptance case

A question such as `Where did Susan Knuckey live?` may have many people actually recorded as Susan Knuckey. A person recorded under another surname but credibly associated with Knuckey through marriage must still remain visible in the association section with an explanation of why the match was made.

## Regression status

651 tests passed in the packaged QA Pass 1 source tree.
