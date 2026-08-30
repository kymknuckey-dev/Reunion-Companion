"""Developer CLI for the normal Ryerson death-research crawler.

The user-facing ``reunion-ryerson`` commands deliberately control the same
crawler as Manage.  The older family-wide targeted bootstrap queue remains
available only through explicitly named inspection commands and is never
started by this CLI.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .database import connect
from .external_evidence_scan import enqueue_death_research_candidates
from .external_research_runner import (
    pause_runner,
    recover_interrupted_runner_state,
    recover_transport_failures,
    runner_status,
    start_runner,
)
from .ryerson_targeted_bootstrap import (
    pause_targeted_bootstrap,
    populate_targeted_queue,
    targeted_status,
)


def default_db_path() -> Path:
    return Path.home()/".reunion-companion"/"companion.sqlite3"


def recent_rows(db, limit=10):
    """Return recent activity from the active death-research crawler."""
    return db.execute(
        """
        SELECT id,person_gedcom_xref,person_name_snapshot,status,attempts,
               result_count,last_error,last_attempt_at,next_retry_at,completed_at
        FROM companion_external_scan_queue
        WHERE source_name='Ryerson' AND last_attempt_at IS NOT NULL
        ORDER BY last_attempt_at DESC, id DESC
        LIMIT ?
        """,
        (int(limit),),
    ).fetchall()


def family_recent_rows(db, limit=10):
    """Return historical activity from the dormant family-wide queue."""
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
    status=runner_status(db)
    print(
        "enabled={enabled} total={total} queued={queued} waiting={retry_wait} "
        "searching={searching} findings={findings} no_finding={no_match} "
        "failed={failed}".format(**status)
    )
    if status.get("source_waiting"):
        print(f"source_waiting=True cooldown_until={status.get('cooldown_until') or ''}")
    family=targeted_status(db)
    print(
        "family_wide_enabled={enabled} total={total} queued={queued} "
        "waiting={retry_wait} searching={searching} completed={completed} "
        "failed={failed}".format(**family)
    )


def print_family_status(db):
    status=targeted_status(db)
    print(
        "enabled={enabled} total={total} queued={queued} waiting={retry_wait} "
        "searching={searching} completed={completed} failed={failed}".format(**status)
    )
    core=", ".join(status.get("core_surnames",[])) or "None"
    print(f"core_surnames={core}")


def _start_normal_runner(db):
    # Normal controls must never wake the legacy family-wide crawler.
    pause_targeted_bootstrap(db)
    recovered=recover_interrupted_runner_state(db)
    transport_recovered=recover_transport_failures(db)
    status=start_runner(db)
    status["recovered_interrupted"]=recovered
    status["recovered_transport_failures"]=transport_recovered
    return status


def _pause_normal_runner(db):
    # Keep the legacy engine dormant even if an old persisted flag survived.
    pause_targeted_bootstrap(db)
    return pause_runner(db)


def main(argv=None):
    ap=argparse.ArgumentParser(prog="reunion-ryerson")
    ap.add_argument(
        "--db",type=Path,default=default_db_path(),
        help="Companion SQLite database",
    )
    sub=ap.add_subparsers(dest="command",required=True)

    sub.add_parser("status",help="show normal death-research crawler status")
    sub.add_parser("start",help="start normal death-research crawler")
    sub.add_parser("pause",help="pause normal death-research crawler")
    sub.add_parser("populate",help="enqueue eligible death-research people")

    recent=sub.add_parser("recent",help="show recent death-research activity")
    recent.add_argument("--limit",type=int,default=10)

    # Explicit inspection-only commands for the retained legacy queue.
    sub.add_parser("family-status",help="inspect dormant family-wide crawler")
    family_recent=sub.add_parser("family-recent",help="inspect dormant family-wide recent activity")
    family_recent.add_argument("--limit",type=int,default=10)
    sub.add_parser("family-populate",help="populate dormant family-wide queue without starting it")

    args=ap.parse_args(argv)
    db=connect(args.db)
    try:
        if args.command=="status":
            print_status(db)
            return 0

        if args.command=="start":
            print(_start_normal_runner(db))
            return 0

        if args.command=="pause":
            print(_pause_normal_runner(db))
            return 0

        if args.command=="populate":
            print({"newly_queued":enqueue_death_research_candidates(db)})
            return 0

        if args.command=="recent":
            print_status(db)
            print()
            for row in recent_rows(db,args.limit):
                print(dict(row))
            return 0

        if args.command=="family-status":
            print_family_status(db)
            return 0

        if args.command=="family-recent":
            print_family_status(db)
            print()
            for row in family_recent_rows(db,args.limit):
                print(dict(row))
            return 0

        if args.command=="family-populate":
            pause_targeted_bootstrap(db)
            print(populate_targeted_queue(db))
            return 0

        return 2
    finally:
        db.close()


if __name__=="__main__":
    raise SystemExit(main())
