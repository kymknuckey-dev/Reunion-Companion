FFD 2.0 RC1.0.14.8.9.9.4.1.3.11 — Selectable Child-only Individuals

Purpose
-------
Extends the child-only individual correction so a terminal child can be
included or omitted explicitly from Family History.

Behaviour
---------
- A child who has no spouse/family record remains visible beneath the parent family.
- The individual now has their own checkbox.
- Terminal individuals are checked by default, preserving the previous inclusion behaviour.
- Unchecking the individual omits that person's Life & Biography section and removes
  that person from the Person, Place and Source indexes for the published book.
- The individual still does not create a family chapter or expandable family branch.
- Existing family checkboxes, Paternal path and Chart only behaviour are unchanged.
- Saved Family History report configurations now retain selected individual IDs.

Regression case
---------------
James Knuckey + Elizabeth Anne Hunter:
Lyell Leonard Knuckey appears as a checked terminal individual and can be
unchecked to exclude him from the report.

QA
--
Targeted .3.9 / .3.10 / .3.11 and packaging regression suite: 8 passed.

Install
-------
Packaged for reunion_companion_install_verify.sh with the required top-level
"Reunion Companion" folder.
