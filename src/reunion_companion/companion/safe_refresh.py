from __future__ import annotations

"""FFD 1.8 Build 1 — Safe GEDCOM Refresh.

Reunion remains authoritative.  A refresh is built and verified in a staging
SQLite database, the working database is backed up, and only then is the stage
atomically promoted.  No row-by-row merge is attempted.
"""

from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any
import hashlib
import json
import os
import shutil
import sqlite3
import tempfile

from .database import connect
from .gedcom import import_gedcom, parse_gedcom
from .beta3_data_manager import ensure_companion_tables, seed_history_from_current, dataset_counts

IMPORTED_TABLES = ("people", "families", "events", "notes", "sources", "media", "citations")
AUTO_REFRESH_BACKUP_RETENTION = 3



@dataclass(frozen=True)
class RefreshValidation:
    integrity: str
    foreign_key_errors: int
    people: int
    families: int
    events: int
    notes: int
    sources: int
    media: int
    citations: int

    @property
    def ok(self) -> bool:
        return self.integrity == "ok" and self.foreign_key_errors == 0 and self.people > 0


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_gedcom_file(path: str | Path) -> dict[str, Any]:
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(str(p))
    if p.stat().st_size == 0:
        raise ValueError("GEDCOM file is empty.")
    roots = parse_gedcom(p)
    indis = sum(1 for r in roots if r.tag == "INDI" and r.xref)
    fams = sum(1 for r in roots if r.tag == "FAM" and r.xref)
    if indis == 0:
        raise ValueError("GEDCOM contains no individual (INDI) records; refresh refused.")
    return {
        "path": str(p),
        "size": p.stat().st_size,
        "mtime": p.stat().st_mtime,
        "sha256": _sha256(p),
        "individuals": indis,
        "families": fams,
    }


def validate_database(db: sqlite3.Connection) -> RefreshValidation:
    integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
    fk = db.execute("PRAGMA foreign_key_check").fetchall()
    counts = dataset_counts(db)
    return RefreshValidation(
        integrity=integrity,
        foreign_key_errors=len(fk),
        people=counts.get("people", 0),
        families=counts.get("families", 0),
        events=counts.get("events", 0),
        notes=counts.get("notes", 0),
        sources=counts.get("sources", 0),
        media=counts.get("media", 0),
        citations=counts.get("citations", 0),
    )


def _rows(db: sqlite3.Connection, sql: str, args=()) -> list[dict[str, Any]]:
    return [dict(r) for r in db.execute(sql, args).fetchall()]


def semantic_snapshot(db: sqlite3.Connection) -> dict[str, Any]:
    """Return a stable, imported-data-only snapshot for change reporting.

    Internal Companion row ids are deliberately excluded. GEDCOM xrefs anchor
    people/families/sources, while person/family content is normalised into
    deterministic tuples. This report is informational; it never drives a merge.
    """
    people: dict[str, Any] = {}
    for p in _rows(db, "SELECT id,gedcom_xref,given_names,surname,display_name,sex,raw_name FROM people ORDER BY gedcom_xref"):
        x = p["gedcom_xref"] or f"id:{p['id']}"
        events = [tuple(r[k] for k in ("event_type","date_text","place_text","value_text","note_text","gedcom_tag"))
                  for r in _rows(db, "SELECT event_type,date_text,place_text,value_text,note_text,gedcom_tag FROM events WHERE person_id=? ORDER BY event_type,date_text,place_text,value_text", (p["id"],))]
        notes = [tuple(r[k] for k in ("note_type","gedcom_tag","gedcom_note_xref","text","is_referenced"))
                 for r in _rows(db, "SELECT note_type,gedcom_tag,gedcom_note_xref,text,is_referenced FROM notes WHERE person_id=? ORDER BY note_type,gedcom_note_xref,text", (p["id"],))]
        fams = [tuple(r[k] for k in ("family_xref","role")) for r in _rows(db, """
            SELECT f.gedcom_xref AS family_xref,fm.role FROM family_members fm
            JOIN families f ON f.id=fm.family_id WHERE fm.person_id=? ORDER BY f.gedcom_xref,fm.role
        """, (p["id"],))]
        people[x] = {
            "identity": (p["given_names"], p["surname"], p["display_name"], p["sex"], p["raw_name"]),
            "events": events,
            "notes": notes,
            "families": fams,
        }

    events: dict[str, Any] = {}
    notes_map: dict[str, Any] = {}
    for p in _rows(db, "SELECT id,gedcom_xref FROM people ORDER BY gedcom_xref"):
        px = p["gedcom_xref"] or f"id:{p['id']}"
        tag_seen: dict[str, int] = {}
        for r in _rows(db, "SELECT id,event_type,date_text,place_text,value_text,note_text,gedcom_tag FROM events WHERE person_id=? ORDER BY id", (p["id"],)):
            tag = r["gedcom_tag"] or r["event_type"] or "EVENT"
            tag_seen[tag] = tag_seen.get(tag, 0) + 1
            key = f"{px}|{tag}|{tag_seen[tag]}"
            events[key] = (r["event_type"],r["date_text"],r["place_text"],r["value_text"],r["note_text"],r["gedcom_tag"])
        note_seen: dict[str, int] = {}
        for r in _rows(db, "SELECT id,note_type,gedcom_tag,gedcom_note_xref,text,is_referenced FROM notes WHERE person_id=? ORDER BY id", (p["id"],)):
            if r["gedcom_note_xref"]:
                key=f"{px}|xref:{r['gedcom_note_xref']}"
            else:
                tag=r["gedcom_tag"] or r["note_type"] or "NOTE"
                note_seen[tag]=note_seen.get(tag,0)+1
                key=f"{px}|{tag}|{note_seen[tag]}"
            notes_map[key]=(r["note_type"],r["gedcom_tag"],r["gedcom_note_xref"],r["text"],r["is_referenced"])

    families: dict[str, Any] = {}
    for f in _rows(db, "SELECT id,gedcom_xref,marriage_date,marriage_place FROM families ORDER BY gedcom_xref"):
        x = f["gedcom_xref"] or f"id:{f['id']}"
        members = [tuple(r[k] for k in ("person_xref","role")) for r in _rows(db, """
            SELECT p.gedcom_xref AS person_xref,fm.role FROM family_members fm
            JOIN people p ON p.id=fm.person_id WHERE fm.family_id=? ORDER BY fm.role,p.gedcom_xref
        """, (f["id"],))]
        families[x] = {"marriage": (f["marriage_date"], f["marriage_place"]), "members": members}

    sources = {
        (r["gedcom_xref"] or f"id:{r['id']}"): (r["title"], r["text"], r["source_type"], r["display_text"])
        for r in _rows(db, "SELECT id,gedcom_xref,title,text,source_type,display_text FROM sources ORDER BY gedcom_xref")
    }

    # Media often has no GEDCOM xref in Reunion exports, so compare a multiset of content signatures.
    media = Counter(tuple(r[k] for k in ("file_path","title","media_type","attachment_scope","attachment_label"))
                    for r in _rows(db, "SELECT file_path,title,media_type,attachment_scope,attachment_label FROM media"))
    return {"people": people, "events": events, "notes": notes_map, "families": families, "sources": sources, "media": media}


def _map_diff(old: dict[str, Any], new: dict[str, Any]) -> dict[str, int]:
    ok, nk = set(old), set(new)
    common = ok & nk
    return {
        "added": len(nk - ok),
        "removed": len(ok - nk),
        "changed": sum(old[k] != new[k] for k in common),
        "unchanged": sum(old[k] == new[k] for k in common),
    }


def compare_snapshots(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    report = {
        "people": _map_diff(old.get("people", {}), new.get("people", {})),
        "events": _map_diff(old.get("events", {}), new.get("events", {})),
        "notes": _map_diff(old.get("notes", {}), new.get("notes", {})),
        "families": _map_diff(old.get("families", {}), new.get("families", {})),
        "sources": _map_diff(old.get("sources", {}), new.get("sources", {})),
    }
    om, nm = old.get("media", Counter()), new.get("media", Counter())
    report["media"] = {
        "added": sum((nm - om).values()),
        "removed": sum((om - nm).values()),
        "changed": 0,
        "unchanged": sum((om & nm).values()),
    }
    return report


def _refresh_backup_files(db_path: Path) -> list[Path]:
    backup_dir = db_path.parent / "backups"
    if not backup_dir.exists():
        return []
    pattern = f"{db_path.stem}-before-refresh-*{db_path.suffix}"
    return sorted(
        (p for p in backup_dir.glob(pattern) if p.is_file()),
        key=lambda p: (p.stat().st_mtime, p.name),
        reverse=True,
    )


def backup_housekeeping_status(db_path: str | Path) -> dict[str, Any]:
    """Describe automatic refresh backups and known stale refresh artefacts.

    Deliberate named checkpoints such as companion-before-ryerson-reset.sqlite3
    are intentionally outside this policy.
    """
    db_path = Path(db_path).expanduser().resolve()
    backups = _refresh_backup_files(db_path)
    excess = backups[AUTO_REFRESH_BACKUP_RETENTION:]
    bickle = db_path.parent / f"{db_path.name}.before-bickle-cleanup"
    stages = [p for p in db_path.parent.glob("reunion-companion-refresh-*.sqlite3") if p.is_file()]
    cleanup = list(excess) + stages + ([bickle] if bickle.is_file() else [])
    return {
        "retention": AUTO_REFRESH_BACKUP_RETENTION,
        "count": len(backups),
        "bytes": sum(p.stat().st_size for p in backups),
        "excess_count": len(excess),
        "excess_bytes": sum(p.stat().st_size for p in excess),
        "stale_stage_count": len(stages),
        "stale_stage_bytes": sum(p.stat().st_size for p in stages),
        "bickle_cleanup_present": bickle.is_file(),
        "bickle_cleanup_bytes": bickle.stat().st_size if bickle.is_file() else 0,
        "cleanup_bytes": sum(p.stat().st_size for p in cleanup),
    }


def prune_refresh_backups(db_path: str | Path, *, retain: int = AUTO_REFRESH_BACKUP_RETENTION) -> list[str]:
    """Keep only the newest automatic Safe Refresh recovery backups."""
    db_path = Path(db_path).expanduser().resolve()
    removed = []
    for path in _refresh_backup_files(db_path)[max(0, int(retain)) :]:
        path.unlink(missing_ok=True)
        removed.append(str(path))
    return removed


def cleanup_refresh_housekeeping(db_path: str | Path) -> dict[str, Any]:
    """Explicit housekeeping for the agreed RC cleanup.

    Keeps three automatic Safe Refresh backups, removes abandoned refresh-stage
    files and the obsolete Bickle cleanup checkpoint. The deliberate Ryerson
    reset checkpoint is never touched.
    """
    db_path = Path(db_path).expanduser().resolve()
    removed = prune_refresh_backups(db_path)
    for path in db_path.parent.glob("reunion-companion-refresh-*.sqlite3"):
        if path.is_file():
            path.unlink(missing_ok=True)
            removed.append(str(path))
    bickle = db_path.parent / f"{db_path.name}.before-bickle-cleanup"
    if bickle.is_file():
        bickle.unlink(missing_ok=True)
        removed.append(str(bickle))
    return {"removed": removed, "removed_count": len(removed), "status": backup_housekeeping_status(db_path)}


def _backup_database(db_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f"{db_path.stem}-before-refresh-{stamp}{db_path.suffix}"
    src = sqlite3.connect(db_path)
    try:
        dst = sqlite3.connect(backup)
        try:
            src.backup(dst)
            dst.commit()
        finally:
            dst.close()
    finally:
        src.close()
    return backup


def _build_stage(db_path: Path, ged: Path) -> tuple[Path, dict[str, Any], dict[str, Any], RefreshValidation]:
    # Clone the current DB so Companion-owned history/publication tables survive,
    # then import_gedcom replaces only the imported dataset.
    # Open the working database read-only in spirit: do not run migrations/history
    # seeding against it. Dry-run must not mutate the working file.
    src = sqlite3.connect(db_path)
    src.row_factory = sqlite3.Row
    before_snapshot = semantic_snapshot(src)
    fd, name = tempfile.mkstemp(prefix="reunion-companion-refresh-", suffix=".sqlite3", dir=str(db_path.parent))
    os.close(fd)
    stage = Path(name)
    clone = sqlite3.connect(stage)
    try:
        src.backup(clone)
        clone.commit()
    finally:
        clone.close()
        src.close()

    work = connect(stage)
    try:
        ensure_companion_tables(work)
        seed_history_from_current(work)
        import_result = import_gedcom(work, ged)
        validation = validate_database(work)
        if not validation.ok:
            raise RuntimeError(
                f"Staged database validation failed: integrity={validation.integrity!r}, "
                f"foreign_key_errors={validation.foreign_key_errors}, people={validation.people}"
            )
        after_snapshot = semantic_snapshot(work)
        # History is written only to the stage. A dry run discards it; a successful
        # promotion carries it into the new working database.
        after_counts=dataset_counts(work)
        before_counts={k:0 for k in after_counts}
        # Counts from the old snapshot are best obtained from the source database
        # before it was closed; derive the principal counts from snapshots here.
        before_counts.update({
            "people":len(before_snapshot.get("people",{})),
            "families":len(before_snapshot.get("families",{})),
            "events":len(before_snapshot.get("events",{})),
            "notes":len(before_snapshot.get("notes",{})),
            "sources":len(before_snapshot.get("sources",{})),
            "media":sum(before_snapshot.get("media",Counter()).values()),
        })
        now=datetime.now().isoformat(timespec="seconds"); stat=ged.stat()
        diff={k:after_counts.get(k,0)-before_counts.get(k,0) for k in after_counts}
        work.execute("""INSERT INTO companion_import_history
          (source_path,imported_at,source_size,source_mtime,source_sha256,counts_json,diff_json,status)
          VALUES(?,?,?,?,?,?,?,?)""",
          (str(ged),now,stat.st_size,stat.st_mtime,_sha256(ged),json.dumps(after_counts),json.dumps(diff),"success"))
        work.commit()
    finally:
        work.close()
    return stage, before_snapshot, after_snapshot, validation


def safe_refresh(db_path: str | Path, gedcom_path: str | Path, *, dry_run: bool = False, reconcile_external: bool = True) -> dict[str, Any]:
    """Build, validate, compare and optionally promote a complete GEDCOM refresh."""
    db_path = Path(db_path).expanduser().resolve()
    ged = Path(gedcom_path).expanduser().resolve()
    source = validate_gedcom_file(ged)
    if not db_path.exists():
        # connect() creates the initial shell. It remains authoritative only after a successful promote.
        db = connect(db_path); db.close()

    stage = None
    try:
        stage, before, after, validation = _build_stage(db_path, ged)
        changes = compare_snapshots(before, after)
        result = {
            "status": "dry-run" if dry_run else "success",
            "source": source,
            "changes": changes,
            "validation": asdict(validation),
            "backup_path": None,
            "promoted": False,
        }
        if dry_run:
            return result

        backup = _backup_database(db_path)
        # os.replace is atomic when source and destination live on the same filesystem;
        # staging is deliberately created beside the working DB for that reason.
        os.replace(stage, db_path)
        stage = None
        result["backup_path"] = str(backup)
        result["promoted"] = True

        # Reconcile Companion-held external discovery state only when refreshing
        # the same active Family File. Family-file switching materialises a
        # different genealogy snapshot and must never retire another family's
        # Ryerson discoveries as ineligible.
        if reconcile_external:
            refreshed = connect(db_path)
            try:
                from .external_evidence_matcher import ryerson_death_candidates
                from .ryerson_discovery_review import (
                    discovery_fact_present_in_reunion,
                    reconcile_discovery_eligibility,
                    reconcile_waiting_discoveries,
                )
                eligible_person_ids = {int(row["person_id"]) for row in ryerson_death_candidates(refreshed)}
                retired = reconcile_discovery_eligibility(refreshed, eligible_person_ids)
                confirmed = reconcile_waiting_discoveries(
                    refreshed,
                    lambda discovery: discovery_fact_present_in_reunion(refreshed, discovery),
                )
                result["discovery_reconciliation"] = {
                    "retired_ineligible": retired,
                    "confirmed_after_refresh": len(confirmed),
                }
            finally:
                refreshed.close()
        else:
            result["discovery_reconciliation"] = {"skipped": "family_file_switch"}

        # A successful verified refresh is the boundary at which automatic
        # recovery-backup retention is safe to enforce. Deliberate named
        # checkpoints are not part of this pruning policy.
        result["pruned_backup_paths"] = prune_refresh_backups(db_path)
        return result
    finally:
        if stage is not None and stage.exists():
            stage.unlink()


def safe_reload_current(db_path: str | Path, *, dry_run: bool = False) -> dict[str, Any]:
    from .beta3_data_manager import current_gedcom
    db = connect(db_path)
    try:
        cur = current_gedcom(db)
    finally:
        db.close()
    if not cur:
        raise RuntimeError("No current GEDCOM is recorded.")
    return safe_refresh(db_path, cur["source_path"], dry_run=dry_run)


def format_change_summary(changes: dict[str, Any]) -> str:
    parts = []
    for kind in ("people", "events", "notes", "families", "sources", "media"):
        d = changes.get(kind, {})
        bits = [f"{k} {d.get(k, 0)}" for k in ("added", "changed", "removed") if d.get(k, 0)]
        if bits:
            parts.append(f"{kind.title()}: " + ", ".join(bits))
    return "; ".join(parts) if parts else "No imported-data changes detected"
