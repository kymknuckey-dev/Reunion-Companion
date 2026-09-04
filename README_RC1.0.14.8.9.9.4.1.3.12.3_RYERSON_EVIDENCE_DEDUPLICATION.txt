FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.3 — Ryerson Evidence Deduplication

Prevents later Ryerson crawler passes from inserting an external-evidence row that
is already stored for the same Reunion person and source finding.

Regression fixture: John Stanley Herbert Bickle (@I4798@), where the same four
Ryerson findings were stored on 25 Aug 2026 and again on 29 Aug 2026 after a
legitimate grouped Bickle, John search rediscovered them.

The grouped surname + first-given-name search strategy is unchanged. Distinct
publication/event dates remain separate findings. Existing duplicate rows are not
deleted by this release; cleanup is intentionally a separate operation so review
state can be preserved safely.
