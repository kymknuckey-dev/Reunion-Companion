# FFD 1.8 Build 2.3.1 — Centralised Version Identity

## Purpose

Prevent the running Reunion Companion application from displaying a stale FFD build number after later releases are installed.

## Behaviour

The running application now reads its user-facing release identity from one module:

`src/reunion_companion/companion/version_identity.py`

That module defines the FFD series, build, release name, accepted release tag and formatted display strings. The web UI header and Terminal startup banner consume those values rather than embedding independent version strings.

Git release tags remain authoritative for `companion-update`; centralised application identity is the authoritative user-facing identity of the code being run.

## Release identity

- FFD series: 1.8
- Build: 2.3.1
- Release: Centralised Version Identity
- Git tag: `ffd-1.8-build-2.3.1`

## Regression protection

Build 2.3.1 adds tests that verify:

- the central release identity is internally consistent;
- the UI displays FFD 1.8 Build 2.3.1;
- stale Build 2.1/2.1.2 strings are absent from the running UI source;
- the startup banner uses the same central identity.
