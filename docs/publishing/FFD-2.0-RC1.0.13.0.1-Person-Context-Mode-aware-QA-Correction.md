# FFD 2.0 RC1.0.13.0.1 — Person Context Mode-aware QA Correction

QA-only correction.

The RC1.0.13 `Current person` test assumed the compact persistent person strip
would render on Presentation Overview. Presentation Overview intentionally uses
the established editorial person hero instead.

The test is now mode-aware/deterministic and verifies the persistent-strip
markup contract without depending on ambient Presentation mode.

No UI, navigation, conversation, genealogy, relationship or publishing
behaviour is changed.
