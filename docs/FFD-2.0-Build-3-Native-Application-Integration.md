# FFD 2.0 Build 3 — Native Application Integration

Build 3 makes normal Companion operation more Mac-native without changing the FFD 1.9 RC1 genealogy engine.

## Added
- Edit menu: Cut, Copy, Paste, Select All.
- View → Reload for the embedded WKWebView.
- Application → Diagnostics showing application/engine identity, backend state, database path, Ollama state/model and backend log location.
- Presentation Biography → Regenerate Biography, explicitly bypassing the existing narrative cache for that request.

Cached Biography remains the default. Regeneration is deliberate, not tied to application builds.

## Preserved
Build 2 native-window navigation, external-link handling, close/reopen behaviour and app-owned backend shutdown.
