# FFD 2.0 RC1.0.5 — Application Identity & Distribution Polish

RC1.0.5 is a visual identity release layered on the proven RC1.0.4 standalone macOS/PDF baseline.

## Scope

- Retain the existing Reunion Companion page structure and top navigation.
- Use the approved **Companion** navy/olive family-tree + book application icon.
- Use a simplified tree/book mark in the existing application header.
- Add a larger Companion identity treatment to the existing Home hero.
- Use the circular tree/book publishing mark on Family History Book title pages.
- Generate a native `.icns` set during the normal macOS application build.
- Keep the existing DMG installation mechanism and PDF runtime unchanged.

## Brand line

**Your family history. Together.**

## Non-goals

This release does not introduce a sidebar, alter global navigation, change genealogy behaviour, or redesign the publishing engine.


## Visual QA Pass 2

- Home body, header sizing and Family History Book publishing mark are locked from Pass 1.
- Tighten only the native macOS app-icon master so the approved artwork fills the icon canvas more effectively.
- Preserve the existing application structure and installation workflow.
- Verify the built bundle and DMG both declare and contain `ReunionCompanion.icns`.
- Judge Finder/Applications and Dock presentation from a fresh installation in `/Applications`, not from a prior installed copy or `/private/tmp`.
- No functional, navigation, genealogy-engine or PDF-runtime changes.
