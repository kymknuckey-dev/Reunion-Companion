# FFD 2.0 Build 5 — Installation & First-Run Experience

Build 5 preserves the FFD 1.9 RC1 genealogy engine and the Build 4 self-contained runtime while making first launch usable without Terminal or the development repository.

## Existing installations
If the Companion database already contains people, startup proceeds directly to the normal application. Existing data is never replaced by first-run setup.

## First run
When no genealogy people are present, the native app presents a Welcome dialog that confirms the bundled runtime and user-data area, checks Ollama and local-model availability, and offers **Import GEDCOM…** or **Continue**.

GEDCOM selection uses a native macOS file chooser. Import is performed by the existing safe-refresh engine; the selected source is then recorded against the active Family File.

## Data safety
User data remains outside the replaceable application at `~/.reunion-companion/`. Build 5 never silently overwrites an existing database.

## Build hygiene
When `build_app.py --install ...` succeeds, the temporary `dist/Reunion Companion.app` build artifact is removed after installation so Spotlight/Launchpad does not retain a second application bundle.

## Preserved
- Embedded self-contained backend runtime.
- FFD 1.9 RC1 genealogy engine.
- Native window, Edit menu, Reload, Diagnostics and Biography regeneration.
- External Ollama service.
- Application-owned backend shutdown.
