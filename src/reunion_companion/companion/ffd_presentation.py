from __future__ import annotations
from pathlib import Path
import json

def _path():
    root=Path.home()/".reunion-companion"
    root.mkdir(parents=True,exist_ok=True)
    return root/"presentation.json"

def presentation_mode_enabled():
    p=_path()
    if not p.exists():
        return False
    try:
        data=json.loads(p.read_text(encoding="utf-8"))
        return bool(data.get("presentation_mode",False))
    except Exception:
        return False

def set_presentation_mode(enabled):
    value=bool(enabled)
    _path().write_text(
        json.dumps({"presentation_mode":value},indent=2),
        encoding="utf-8"
    )
    return value

def toggle_presentation_mode():
    return set_presentation_mode(not presentation_mode_enabled())
