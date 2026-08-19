# FFD 2.0 RC1.0.8 — Publishing Runtime Hardening QA Pass 1

## Scope

This pass repairs a frozen macOS publishing regression in which Family History Book PDF publishing could fail during a late WeasyPrint import with `LookupError: unknown encoding: utf-16le`, despite the codec modules being present in PyInstaller `base_library.zip` and the simple frozen PDF probe succeeding.

## Changes

- Initialise the `utf-16le` codec at frozen backend startup.
- Eagerly import WeasyPrint before the long-running Companion server starts.
- Extend the frozen PDF verification path to exercise UTF-16LE plus representative book typography.
- Preserve a complete traceback in the backend log when PDF-runtime loading fails, while retaining the concise UI error.
- No Family History Book layout, biography, media, or genealogy changes are included.

## Acceptance

The packaged macOS app must pass `--verify-pdf-runtime` and successfully publish a real Family History Book PDF from the application UI.
