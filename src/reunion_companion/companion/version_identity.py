"""Authoritative user-facing Reunion Companion release identity.

Git release tags remain authoritative for deployment/update selection.  This
module is the single source used by the running application when it identifies
itself to a user.
"""
from __future__ import annotations

FFD_SERIES = "1.8"
FFD_BUILD = "2.3.1"
RELEASE_NAME = "Centralised Version Identity"
RELEASE_TAG = "ffd-1.8-build-2.3.1"
FFD_DISPLAY = f"FFD {FFD_SERIES} Build {FFD_BUILD}"
APP_DISPLAY_NAME = f"Reunion Companion — {FFD_DISPLAY} {RELEASE_NAME}"


def release_identity() -> dict[str, str]:
    return {
        "series": FFD_SERIES,
        "build": FFD_BUILD,
        "name": RELEASE_NAME,
        "tag": RELEASE_TAG,
        "display": FFD_DISPLAY,
        "application": APP_DISPLAY_NAME,
    }
