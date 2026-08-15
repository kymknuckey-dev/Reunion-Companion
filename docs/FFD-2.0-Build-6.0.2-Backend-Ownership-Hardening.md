# FFD 2.0 Build 6.0.2 — Backend Ownership Hardening

Genealogy engine baseline: **FFD 1.9 RC1**.

This maintenance build prevents the native application from silently attaching to a stale or foreign service already listening on Companion's localhost port.

## Contract

- The backend exposes `GET /runtime/identity` with a stable service marker, protocol version, application build, release name, and genealogy-engine baseline.
- The native launcher accepts an already-running backend only when its service, protocol, application build, and engine baseline match Build 6.0.2.
- If port 8765 is occupied by an older Companion backend or another service, the launcher refuses to attach and presents a native startup error. It never kills an unidentified process.
- A backend launched by the current native process remains owned through its `Process` object and is stopped on normal application termination.
- A compatible backend that was already running is not adopted as an owned `Process` and therefore is not terminated by this launcher.

No genealogy, Biography, Research, Publishing, GEDCOM, database, media, or presentation semantics are intentionally changed.
