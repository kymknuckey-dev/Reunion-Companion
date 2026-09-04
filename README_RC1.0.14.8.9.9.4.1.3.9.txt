FFD 2.0 RC1.0.14.8.9.9.4.1.3.9 — Child-only Individual Family-history Inclusion

Purpose
-------
Corrects Family History publishing so a child who never forms a recorded
spouse/family record is not omitted from the report.

Behaviour
---------
- Family branch/chapter selection remains family-based.
- Children who form a family continue to be represented by their family chapter.
- Children who do not form a family are emitted as terminal individual Life &
  Biography sections in their parents' family chapter.
- Terminal children are included in the Person Index, Place Index and Source Index.
- Existing paternal-path, chart-only and hierarchical family ordering behaviour
  is unchanged.

Regression case
---------------
James Knuckey + Elizabeth Anne Hunter:
Lyell Leonard Knuckey must remain in the Family History even though he has no
formed family record.

QA
--
Targeted affected/regression suite: 10 passed.
Full suite: 1264 passed, with 2 failures observed initially:
1. production packaging metadata expected the prior release identity — corrected
   in this patch and subsequently passing;
2. pre-existing Ryerson pagination-controls test failure, unrelated to this change.

Apply
-----
Overlay this ZIP at the Reunion Companion repository root, preserving paths,
then run the normal test/build/install verification workflow.
