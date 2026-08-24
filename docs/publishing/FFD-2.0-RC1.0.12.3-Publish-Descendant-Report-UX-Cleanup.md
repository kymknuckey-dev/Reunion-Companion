# FFD 2.0 RC1.0.12.3 — Publish & Descendant Report UX Cleanup

## Scope

UX and presentation only. The accepted Descendant Report renderer, genealogy and 1–6 generation limit remain unchanged.

## Person > Publish

- Present report actions as a consistent two-column tile grid.
- Research Profile, Biography, Person Report, Descendant Report and Family-history Book use one visual language.
- Descendant Report receives a clear primary action treatment.
- Family-history Book no longer appears as an oversized full-width button merely because of legacy styling.
- Add concise helper text describing each report.
- Present recorded spouse families as clean family cards with marriage/descendant summary where available.
- Each family card has an explicit **Descendant Report…** action.

## Descendant Report configuration

- If launched from a specific family, that family is fixed and displayed as context rather than shown as a redundant selector.
- If the person has exactly one spouse family, it is also fixed automatically.
- Only a generic launch for a person with multiple spouse families asks the user to choose a starting family.
- Generations use a clear 1–6 dropdown.
- Show a plain-language summary of what the chosen depth includes.
- Keep **Create Print-ready PDF** and **Create HTML** as the two output actions.
- Preserve the report-generation progress indicator.

## Regression boundary

Do not change:
- standalone Descendant Report body layout or genealogy;
- History Book family scope;
- Family & Descendants embedded chart data;
- Spouse Family & Descendants data or layout;
- RC1.0.10 multi-page PDF reproduction.
