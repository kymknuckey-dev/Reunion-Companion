"""Developer CLI for the active hybrid targeted Ryerson bootstrap runner."""

from __future__ import annotations

import argparse
from pathlib import Path

from .database import connect
from .ryerson_targeted_bootstrap import (
    pause_targeted_bootstrap,
    populate_targeted_queue,
    start_targeted_bootstrap,
    targeted_status,
)


def default_db_path() -> Path:
    return Path.home()/".reunion-companion"/"companion.sqlite3"


def recent_rows(db, limit=10):
    return db.execute(
        """
        SELECT search_kind,surname,given_name,search_key,status,attempts,
               result_count,match_count,last_error,last_attempt_at,
               next_retry_at,completed_at
        FROM companion_ryerson_targeted_queue
        WHERE status <> 'queued'
        ORDER BY COALESCE(last_attempt_at,completed_at,updated_at) DESC
        LIMIT ?
        """,
        (int(limit),),
    ).fetchall()


def print_status(db):
    status=targeted_status(db)
    print(
        "enabled={enabled} total={total} queued={queued} waiting={retry_wait} "
        "searching={searching} completed={completed} failed={failed}".format(**status)
    )
    core=", ".join(status.get("core_surnames",[])) or "None"
    print(f"core_surnames={core}")


def main(argv=None):
    ap=argparse.ArgumentParser(prog="reunion-ryerson")
    ap.add_argument(
        "--db",type=Path,default=default_db_path(),
        help="Companion SQLite database",
    )
    sub=ap.add_subparsers(dest="command",required=True)

    sub.add_parser("status")
    sub.add_parser("start")
    sub.add_parser("pause")
    sub.add_parser("populate")

    recent=sub.add_parser("recent")
    recent.add_argument("--limit",type=int,default=10)

    args=ap.parse_args(argv)
    db=connect(args.db)
    try:
        if args.command=="status":
            print_status(db)
            return 0

        if args.command=="start":
            print(start_targeted_bootstrap(db))
            return 0

        if args.command=="pause":
            print(pause_targeted_bootstrap(db))
            return 0

        if args.command=="populate":
            print(populate_targeted_queue(db))
            return 0

        if args.command=="recent":
            print_status(db)
            print()
            for row in recent_rows(db,args.limit):
                print(dict(row))
            return 0

        return 2
    finally:
        db.close()


if __name__=="__main__":
    raise SystemExit(main())
