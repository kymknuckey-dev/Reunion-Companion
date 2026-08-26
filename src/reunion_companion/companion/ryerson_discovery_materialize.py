from __future__ import annotations

import sqlite3
from typing import Any

from .ryerson_discovery_assembly import assemble_discoveries


def _tables(db):
    return {
        row[0]
        for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }


def _columns(db, table):
    return {
        row[1]
        for row in db.execute(f'PRAGMA table_info("{table}")').fetchall()
    }


def _first(cols, *names):
    for name in names:
        if name in cols:
            return name
    return None


def _candidate_tables(db):
    """Find only tables capable of representing person-to-notice relationships.

    Queue/search summary tables are deliberately excluded: result_count and
    match_count are never sufficient to create a discovery.
    """
    candidates=[]
    for table in sorted(_tables(db)):
        low=table.casefold()
        if "ryerson" not in low and "external_notice" not in low:
            continue
        cols=_columns(db,table)
        person=_first(cols,"person_id","reunion_person_id")
        notice=_first(
            cols,
            "notice_id","external_record_key","source_record_id",
            "ryerson_id","record_id",
        )
        if not person or not notice:
            continue
        if not (
            "match" in low
            or "candidate" in low
            or "membership" in low
            or "evidence" in low
        ):
            continue
        candidates.append((table,cols,person,notice))
    return candidates


def _rows_from_table(db, table, cols, person_col, notice_col):
    select=[f'"{person_col}" AS person_id', f'"{notice_col}" AS notice_id']
    aliases={
        "surname":("surname","last_name"),
        "given_name":("given_name","first_name","given_names"),
        "death_date":("death_date","event_date"),
        "funeral_date":("funeral_date",),
        "publication_date":("publication_date","published_date"),
        "newspaper":("newspaper","publication"),
        "notice_type":("notice_type","type"),
        "match_status":("match_status","status"),
        "match_confidence":("match_confidence","confidence"),
        "match_reason":("match_reason","reason"),
    }
    for alias,names in aliases.items():
        col=_first(cols,*names)
        if col:
            select.append(f'"{col}" AS "{alias}"')

    sql=f'SELECT {", ".join(select)} FROM "{table}" WHERE "{person_col}" IS NOT NULL AND "{notice_col}" IS NOT NULL'
    return [dict(row) for row in db.execute(sql).fetchall()]


def materialize_existing_ryerson_discoveries(db):
    """Materialise real persisted person/notice relationships into review work.

    This is intentionally conservative. If the current database does not expose
    a table containing both a concrete Reunion person id and a concrete notice
    id, nothing is created. Raw queue counts are never expanded into discoveries.
    """
    sources=[]
    candidates=[]
    seen=set()

    for table,cols,person_col,notice_col in _candidate_tables(db):
        rows=_rows_from_table(db,table,cols,person_col,notice_col)
        accepted=0
        for row in rows:
            key=(row.get("person_id"),row.get("notice_id"))
            if key in seen:
                continue
            seen.add(key)
            candidates.append(row)
            accepted+=1
        sources.append({"table":table,"rows":len(rows),"unique_relationships":accepted})

    result=assemble_discoveries(db,candidates)
    return {
        "source_tables":sources,
        "candidate_relationships":len(candidates),
        "assembled_count":result["assembled_count"],
        "skipped_count":result["skipped_count"],
    }
