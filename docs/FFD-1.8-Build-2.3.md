# FFD 1.8 Build 2.3 — Installed Commands & Safe Release Updating

## Purpose
Make a portable Reunion Companion installation simple to launch and maintain on deployment Macs without requiring the user to remember repository, virtual-environment or Git commands.

## Installed commands

- `companion` launches the local Companion UI using the installation's own `.venv`.
- `companion-update` checks GitHub for the newest accepted `ffd-*` release tag, refuses to overwrite a dirty checkout, asks before changing releases, updates Python dependencies, runs the regression suite, and leaves `~/.reunion-companion` untouched.

Commands are installed to `~/.local/bin`. The installer adds that directory to `.zprofile` once, between clearly marked Reunion Companion lines.

## Release policy
Deployment Macs follow accepted `ffd-*` tags. Tags containing `wip` are ignored. The development branch itself is never treated as an automatic deployment release.

## Failure safety
If update verification fails after checkout, the updater attempts to return to the previous Git revision and reinstall its dependencies. Family Files, GEDCOMs, reports and Companion backups are outside the source checkout and are not modified by the updater.

## Portable bootstrap
`tools/bootstrap_portable_mac.py --install-commands` installs the two user commands after the project venv exists.
