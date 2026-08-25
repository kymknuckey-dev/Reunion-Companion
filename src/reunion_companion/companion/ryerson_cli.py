"""Developer CLI for the Ryerson surname bootstrap runner."""

from __future__ import annotations

import argparse
from pathlib import Path

from .database import connect
from .ryerson_surname_bootstrap import bootstrap_status,pause_bootstrap,start_bootstrap


def default_db_path() -> Path:
    return Path.home()/".reunion-companion"/"companion.sqlite3"


def recent_rows(db, limit=10):
    return db.execute(
        """
        SELECT surname,status,attempts,result_count,match_count,
               last_error,last_attempt_at,next_retry_at,completed_at
        FROM companion_ryerson_surname_queue
        WHERE status <> 'queued'
        ORDER BY COALESCE(last_attempt_at,completed_at,updated_at) DESC
        LIMIT ?
        """,
        (int(limit),),
    ).fetchall()


def print_status(db):
    status=bootstrap_status(db)
    print(
        "enabled={enabled} total={total} queued={queued} "
        "waiting={retry_wait} completed={completed} failed={failed}".format(**status)
    )


def main(argv=None):
    ap=argparse.ArgumentParser(prog="reunion-ryerson")
    ap.add_argument("--db",type=Path,default=default_db_path(),help="Companion SQLite database")
    sub=ap.add_subparsers(dest="command",required=True)
    sub.add_parser("start")
    sub.add_parser("pause")
    sub.add_parser("status")
    recent=sub.add_parser("recent")
    recent.add_argument("-n","--limit",type=int,default=10)
    args=ap.parse_args(argv)

    db=connect(args.db)
    try:
        if args.command=="start":
            print(start_bootstrap(db))
        elif args.command=="pause":
            print(pause_bootstrap(db))
        elif args.command=="status":
            print_status(db)
        elif args.command=="recent":
            print_status(db)
            print()
            for row in recent_rows(db,args.limit):
                print(dict(row))
    finally:
        db.close()


if __name__=="__main__":
    main()
