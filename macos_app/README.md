# FFD 2.0 Build 1 — macOS Application Foundation

Build 1 adds a native AppKit launcher around the frozen FFD 1.9 RC1 genealogy engine.

The app launches the repository `.venv` without Terminal, waits until Companion responds,
opens the existing browser UI, prevents duplicate backend startup when Companion is already
running, shuts down a backend process it owns when the app quits, and writes backend logs to
`~/Library/Logs/Reunion Companion/backend.log`.

This build is not yet a self-contained distribution. It intentionally depends on the
development repository and `.venv`. Runtime bundling, native content windows, settings,
signing/notarisation, DMG packaging, and updater UX are later FFD 2.0 work.
