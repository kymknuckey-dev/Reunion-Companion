# FFD 2.0 RC1.0.12.2 — Descendant Report Controls & Presentation QA

## Purpose

Promote the accepted standalone Descendant Report from preview status to a normal Publish feature without changing the approved report body layout.

## Controls

From Person > Publish:

- **Descendant Report…** opens the standalone report configuration page.
- Choose the starting spouse/family when more than one family is recorded.
- Choose **1–6 generations**.
- Generation 1 is the selected starting couple.
- Create either **HTML** or **Print-ready PDF**.

Each family listed on Person > Publish also links directly to the same configuration page with that family preselected.

The family workspace also links to the same configuration page.

## Presentation QA

- Preserve the accepted indented descendant-report body.
- Give the Reunion Companion publishing mark an explicit 28 mm square maximum presentation size.
- Names remain primary and dates secondary.
- No decorative colour dependency.
- HTML and PDF share the same report source.

## Publish cleanup

The misleading **Family Report (HTML)** control is removed from Person > Publish and replaced by **Descendant Report…**.

The older family-report backend remains untouched for compatibility but is no longer presented as the normal Publish choice.

## Regression boundary

Do not modify:
- History Book family scope;
- Family & Descendants embedded chart data;
- Spouse Family & Descendants data or layout;
- RC1.0.10 multi-page PDF reproduction.
