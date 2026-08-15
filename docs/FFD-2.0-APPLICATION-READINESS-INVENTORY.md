# FFD 2.0 Application Readiness Inventory

This is an inventory, not an FFD 1.9 implementation plan. Its purpose is to identify development-era surfaces that FFD 2.0 must hide behind a normal macOS application experience.

## Target experience

Normal use begins by opening `Reunion Companion.app`. Terminal, Python, virtual environments, localhost ports and CLI commands are not part of the ordinary user workflow. The CLI remains available underneath for diagnostics and development.

## Surfaces to absorb into the application

### Startup and shutdown
- Replace manual virtual-environment activation and `companion` launch with application lifecycle management.
- Start the local Companion service automatically and wait for readiness.
- Avoid exposing the localhost port to the user.
- Shut down application-owned processes cleanly.

### User interface host
- Initial low-risk option: application launch manages the existing UI and browser opening.
- Later evaluate a dedicated macOS application window without rewriting the genealogy engine.

### Family data lifecycle
- Surface GEDCOM selection/refresh in the application.
- Show refresh progress, success/failure and backup/result information without Terminal.
- Preserve the current safe refresh behaviour.

### AI runtime
- Detect local LLM/Ollama availability automatically.
- Present useful application-level status and recovery guidance.
- Keep model/runtime details out of normal genealogy workflows unless attention is required.

### Database and files
- Manage database location and family-file configuration through application settings.
- Provide diagnostics for missing/inaccessible files without requiring shell commands.

### Publishing
- Keep publishing accessible from the application with progress and actionable failures.

### Diagnostics
- Retain CLI and diagnostic commands underneath the app.
- Add an application Diagnostics/About surface for version, database, AI/runtime and support information.

### Distribution and updates
- Produce a double-clickable macOS `.app` first.
- Establish repeatable packaging.
- Later move toward normal Mac distribution/update mechanics so the MacBook does not require a development install workflow.

## FFD 2.0 design rule

If an ordinary genealogy task requires Terminal, that task has not yet been fully applicationised.
