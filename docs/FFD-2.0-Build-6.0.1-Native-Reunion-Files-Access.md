# FFD 2.0 Build 6.0.1 — Native Reunion Files Access

Repairs external Reunion media access exposed by DMG installation in `/Applications`.

The native shell now offers **Reunion Files Access…**, obtains folder access through a macOS directory chooser, stores a security-scoped bookmark in the Companion user-data directory, restores that scope on later launches, and exposes the granted path in Diagnostics. Media permission failures return HTTP 403 rather than repeated Python tracebacks.

No database, GEDCOM, genealogy-engine, or Biography synthesis rules are changed.
