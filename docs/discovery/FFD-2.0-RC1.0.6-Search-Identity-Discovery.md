# FFD 2.0 RC1.0.6 — Search & Identity Discovery

## Objective
Make the Search entry point work the way a new family user naturally expects: find a person by the name they know, or ask a person-anchored natural-language question before selecting a Person page.

## Behaviour

- Search is presented as **Search the Family**.
- The same field accepts a recorded person name or a natural-language question.
- A question such as `Where did Susan Knuckey live?` can resolve the named person before any person focus exists.
- Reunion's recorded identity remains authoritative.
- A spouse surname is a search association only. It does not assert that the person adopted that surname.
- Conservative given-name variants can assist discovery, for example Sue/Susan.
- Exact recorded names rank ahead of inferred associations.
- Ambiguous candidates remain explicit and selectable; question-relevant evidence affects ranking but never removes other credible candidates.
- Search results explain inferred identity associations and link to the canonical Reunion person.
- Existing conventional person search remains supported.

## Initial boundary
This release handles questions containing an identifiable person-name anchor. Family-wide semantic questions such as “Who in the family worked in Cornwall?” remain future work.
