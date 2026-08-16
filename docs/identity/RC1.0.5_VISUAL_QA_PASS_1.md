# FFD 2.0 RC1.0.5 — Visual QA Pass 1

This pass is deliberately visual only. It preserves the existing Reunion Companion page structure, top navigation, publishing behaviour, and the proven standalone PDF runtime.

Changes from the first RC1.0.5 visual build:

- Family History Book publishing mark enlarged and tightly framed so the mark reads as deliberate cover branding.
- Existing Home body branding retained unchanged.
- Existing top banner structure retained; the header mark is tightly framed and displayed larger.
- macOS application icon artwork enlarged inside its 1024 × 1024 icon canvas while preserving the approved Companion artwork.
- Existing `CFBundleIconFile`/`.icns` build path retained. Applications/Finder verification is to be performed from the packaged DMG installation, rather than from an older installed application while testing `/private/tmp`.

Acceptance checks:

1. Header mark is clearly visible at normal application scale.
2. Home body branding remains visually unchanged from the approved first pass.
3. Family History Book cover mark is materially larger and readable.
4. Dock icon uses more of the available visual area.
5. A fresh DMG installation into `/Applications` shows the Companion icon in Finder/Applications.
6. Frozen PDF runtime still reports `Frozen PDF runtime OK`.
