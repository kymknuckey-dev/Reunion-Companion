# FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.6.6 — External Evidence Identity & Review Lifecycle Correction

This release corrects two external-evidence integrity cases found in live data.

* A Ryerson source record has one durable review lifecycle even if Companion later changes its proposed-fact interpretation. Reviewed evidence is not recreated as New.
* Historical exact duplicate external-evidence rows are consolidated to the oldest canonical evidence row. Existing review decisions are retained and references are repointed before duplicate evidence rows are removed.

Validated cases model John Stanley Herbert (Jack) Bickle publication-only reinterpretation and Brian Victor Knuckey repeated identical Ryerson evidence.
