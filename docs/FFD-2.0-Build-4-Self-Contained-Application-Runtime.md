# FFD 2.0 Build 4 — Self-Contained Application Runtime

Build 4 removes the installed application's dependency on the development repository and `.venv`.

## Runtime architecture

The build process uses PyInstaller in `onedir` mode to freeze the Companion backend and its Python dependencies into `Reunion Companion.app/Contents/Resources/Runtime`. The Swift launcher starts that bundled executable directly.

The development `.venv` is still a **build tool**, but is not required to run the installed application.

## Preserved externally

User state is deliberately not embedded in the replaceable application bundle:

- database: `~/.reunion-companion/companion.sqlite3`
- configuration/cache: `~/.reunion-companion/`
- logs: `~/Library/Logs/Reunion Companion/`
- Ollama: external local service

## Build dependency

Build 4 requires PyInstaller in the development virtual environment:

    python -m pip install PyInstaller

## Acceptance target

After building and installing the app, temporarily make the development repository unavailable. The installed app must still launch its backend and support normal Home/Search/person navigation, Biography, Research and representative publishing. Diagnostics must show a runtime path inside the application bundle.
