#!/usr/bin/env python3
"""Safe deployment updater for Reunion Companion.

Deployment machines follow accepted annotated/lightweight FFD tags, never the
feature development branch. Local Family File data under ~/.reunion-companion
is intentionally outside the Git checkout and is never modified here.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import os
import re
import subprocess
import sys

TAG_RE = re.compile(r"^ffd-\d+(?:\.\d+)*-build-[0-9A-Za-z.]+$")


def run(repo: Path, *args: str, check: bool = True, capture: bool = False):
    return subprocess.run(
        list(args), cwd=repo, check=check, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def output(repo: Path, *args: str) -> str:
    return run(repo, *args, capture=True).stdout.strip()


def ensure_repo(repo: Path) -> None:
    if not (repo / ".git").exists():
        raise RuntimeError(f"Not a Git checkout: {repo}")


def worktree_clean(repo: Path) -> bool:
    return output(repo, "git", "status", "--porcelain") == ""


def accepted_tags(repo: Path) -> list[str]:
    raw = output(repo, "git", "tag", "--list", "ffd-*", "--sort=-version:refname")
    tags = []
    for tag in raw.splitlines():
        t = tag.strip()
        if not t or "wip" in t.casefold():
            continue
        if TAG_RE.match(t):
            tags.append(t)
    return tags


def current_release(repo: Path) -> str | None:
    tags = output(repo, "git", "tag", "--points-at", "HEAD").splitlines()
    accepted = set(accepted_tags(repo))
    for tag in tags:
        if tag in accepted:
            return tag
    return None


def friendly(tag: str | None) -> str:
    if not tag:
        return "unreleased checkout"
    m = re.match(r"ffd-([0-9.]+)-build-(.+)$", tag)
    return f"FFD {m.group(1)} Build {m.group(2)}" if m else tag


def latest_release(repo: Path, fetch: bool = True) -> str:
    if fetch:
        run(repo, "git", "fetch", "--tags", "--prune", "origin")
    tags = accepted_tags(repo)
    if not tags:
        raise RuntimeError("No accepted FFD release tags were found.")
    return tags[0]


def python_for(repo: Path) -> Path:
    p = repo / ".venv" / "bin" / "python"
    if not p.exists():
        raise RuntimeError(f"Virtual environment not found: {p}")
    return p


def update(repo: Path, assume_yes: bool = False, check_only: bool = False,
           skip_tests: bool = False) -> int:
    ensure_repo(repo)
    print("Reunion Companion Updater\n")
    if not worktree_clean(repo):
        print("Update stopped. Local source changes were found and have not been overwritten.")
        print("\n" + output(repo, "git", "status", "--short"))
        return 3

    old_commit = output(repo, "git", "rev-parse", "HEAD")
    old_release = current_release(repo)
    latest = latest_release(repo, fetch=True)
    print("Installed:", friendly(old_release))
    print("Latest accepted release:", friendly(latest))

    if old_release == latest:
        print("\nReunion Companion is already current.")
        return 0
    if check_only:
        print("\nAn accepted update is available.")
        return 10

    if not assume_yes:
        reply = input(f"\nUpdate {friendly(old_release)} → {friendly(latest)}? [y/N] ").strip().casefold()
        if reply not in {"y", "yes"}:
            print("Update cancelled. Nothing was changed.")
            return 0

    py = python_for(repo)
    try:
        print("\nUpdating source...")
        run(repo, "git", "checkout", "--detach", latest)
        print("Updating Python dependencies...")
        run(repo, str(py), "-m", "pip", "install", "-e", ".")
        if not skip_tests:
            print("Running regression suite...")
            run(repo, str(py), "-m", "pytest", "-q")
    except Exception as exc:
        print(f"\nUpdate verification failed: {exc}")
        print("Restoring the previous source revision...")
        try:
            run(repo, "git", "checkout", "--detach", old_commit)
            run(repo, str(py), "-m", "pip", "install", "-e", ".")
            print("Previous source revision restored.")
        except Exception as rollback_exc:
            print("Rollback also failed:", rollback_exc)
        return 4

    print(f"\nReunion Companion is now {friendly(latest)}.")
    print("Your Family Files and local data were not changed.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--yes", action="store_true", help="accept the update without prompting")
    ap.add_argument("--check", action="store_true", help="check for a newer accepted release only")
    ap.add_argument("--skip-tests", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    try:
        return update(a.repo.expanduser().resolve(), a.yes, a.check, a.skip_tests)
    except Exception as exc:
        print("Update failed; nothing was intentionally changed.", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
