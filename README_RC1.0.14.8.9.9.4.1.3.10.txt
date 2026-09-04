FFD 2.0 RC1.0.14.8.9.9.4.1.3.10 — Family Scope Child-only Individual Visibility

Purpose
-------
Corrects the Family-history Book Scope selector so children who never form a
recorded spouse/family are visible as terminal individuals.

Behaviour
---------
- Existing family rows, checkboxes, Paternal path and Chart only badges remain unchanged.
- A child with no spouse/family record is shown beneath the parent family as:
  Individual — no family branch
- Terminal individuals have no family checkbox because there is no family chapter to select.
- They remain automatically included with their parent family in publication.
- This complements RC1.0.14.8.9.9.4.1.3.9, which already corrected the published report.

Regression case
---------------
James Knuckey + Elizabeth Anne Hunter:
Lyell Leonard Knuckey is now visible in the scope selector even though he has
no formed family record.

QA
--
Targeted scope/publishing regression suite: 14 passed.

Install
-------
This ZIP is packaged for reunion_companion_install_verify.sh and contains the
required top-level "Reunion Companion" folder.
