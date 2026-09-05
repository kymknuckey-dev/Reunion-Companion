# FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.6 — Research Value Prioritisation

Adds an explainable Research Value ordering to External Evidence Review alongside Most Recent and Relationship.

Research Value is calculated from currently `new` discovery candidates against the current Reunion snapshot. It does not change Reunion data or review state.

Initial assessment classes:
- High opportunity — a definite new Ryerson Death candidate can fill a missing Death or matches an existing unsourced Reunion Death.
- Potential opportunity — current evidence may add useful context but does not directly confirm the recorded Death.
- Needs careful review — a definite Death candidate conflicts with the definite Death currently recorded in Reunion.
- Lower immediate value — no obvious current Death gap is strengthened by the current new candidates.

GEDCOM/Ryerson definite dates use the existing `_definite_date()` normalisation, so forms such as `11 MAR 2003` and `11MAR2003` compare as the same date.

Processed evidence cannot raise current Research Value because assessment is based only on the active review-state candidate group.

Improve/Data Quality Centre is intentionally unchanged in this release. The live Research Value ordering will be evaluated before that page is redesigned around the same assessment.

Regression suite: 1298 passed.
