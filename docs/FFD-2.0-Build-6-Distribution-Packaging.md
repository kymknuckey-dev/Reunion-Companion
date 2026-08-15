# FFD 2.0 Build 6 — Distribution Packaging

Build 6 packages the accepted self-contained, first-run-capable application into a compressed macOS DMG. The DMG contains Reunion Companion.app, an Applications shortcut, and concise installation instructions. The application is built into temporary staging so no duplicate discoverable app remains under the repository. The DMG is verified by hdiutil and mounted read-only to validate its contents and embedded runtime.

Developer ID signing, Hardened Runtime and Apple notarisation are deliberately deferred to a later build. The genealogy engine remains FFD 1.9 RC1.
