#!/usr/bin/env python3
"""Install simple user commands: companion and companion-update."""
from __future__ import annotations
from pathlib import Path
import argparse, os, shlex

MARKER_BEGIN = "# >>> Reunion Companion commands >>>"
MARKER_END = "# <<< Reunion Companion commands <<<"


def shell_quote(p: Path) -> str:
    return shlex.quote(str(p))


def install(repo: Path, bin_dir: Path, update_profile: bool = True) -> tuple[Path, Path]:
    repo = repo.resolve(); bin_dir = bin_dir.expanduser().resolve()
    py = repo / ".venv" / "bin" / "python"
    if not py.exists():
        raise RuntimeError(f"Create the project virtual environment first: {py}")
    if not (repo / "tools" / "companion_update.py").exists():
        raise RuntimeError("companion_update.py is missing from this installation")
    bin_dir.mkdir(parents=True, exist_ok=True)

    companion = bin_dir / "companion"
    companion.write_text(
        "#!/bin/sh\n"
        f"exec {shell_quote(py)} -m reunion_companion.companion.ui \"$@\"\n",
        encoding="utf-8",
    )
    updater = bin_dir / "companion-update"
    updater.write_text(
        "#!/bin/sh\n"
        f"exec {shell_quote(py)} {shell_quote(repo / 'tools' / 'companion_update.py')} --repo {shell_quote(repo)} \"$@\"\n",
        encoding="utf-8",
    )
    companion.chmod(0o755); updater.chmod(0o755)

    if update_profile:
        profile = Path.home() / ".zprofile"
        text = profile.read_text(encoding="utf-8") if profile.exists() else ""
        block = f'{MARKER_BEGIN}\nexport PATH="{bin_dir}:$PATH"\n{MARKER_END}'
        if MARKER_BEGIN not in text:
            if text and not text.endswith("\n"): text += "\n"
            profile.write_text(text + block + "\n", encoding="utf-8")
    return companion, updater


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--bin-dir", default=str(Path.home()/".local"/"bin"))
    ap.add_argument("--no-profile", action="store_true")
    a=ap.parse_args()
    try:
        companion, updater = install(Path(a.repo), Path(a.bin_dir), not a.no_profile)
    except Exception as exc:
        print("Command installation failed:", exc)
        return 2
    print("Installed:", companion)
    print("Installed:", updater)
    print("Open a new Terminal window, or run:")
    print(f'export PATH="{Path(a.bin_dir).expanduser().resolve()}:$PATH"')
    print("Then use: companion   or   companion-update")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
