# FFD 2.0 RC1.0.5 — Application Identity & Distribution Polish

This release applies the approved Reunion Companion visual identity without changing the existing Companion site structure, top navigation, genealogy behaviour, database/import workflows, conversation behaviour, or publishing engine.

## Approved identity system

- **macOS application icon:** text-free navy Companion artwork combining a family tree, four people, landscape and open book.
- **In-app branding:** the approved navy/green Reunion Companion logo and the line “Your family history. Together.”
- **Application header:** the simplified tree-and-book mark inside the existing top header. Navigation remains exactly where it was.
- **Publishing:** the restrained circular tree-and-book mark on Family History title pages.
- **Distribution:** the application bundle carries the production icon so Finder, Dock, Applications and DMG views share the same identity.

## Release boundary

RC1.0.4 remains the functional baseline. RC1.0.5 is visual and distribution polish only. The standalone WeasyPrint/Pango/HarfBuzz PDF runtime from RC1.0.4 is intentionally retained unchanged.

## Installation workflow

RC1.0.5 uses the established Reunion Companion workflow: expand the release under `/Users/kymknuckey/Downloads/Reunion Companion Dev`, overlay the release source onto `/Users/kymknuckey/Development/Reunion Companion`, retain the existing `.git` and `.venv`, run the tests, then build/package using the existing macOS builder and DMG packager.
