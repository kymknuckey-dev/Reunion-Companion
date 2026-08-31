from __future__ import annotations

from datetime import datetime, timezone
import json


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_report_configuration_schema(db) -> None:
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS companion_report_configurations (
            id INTEGER PRIMARY KEY,
            report_type TEXT NOT NULL,
            start_person_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            settings_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(report_type, start_person_id, name)
        )
        """
    )
    db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_companion_report_configurations_lookup
        ON companion_report_configurations(report_type, start_person_id, name)
        """
    )
    db.commit()


def _decode(row):
    if row is None:
        return None
    item = dict(row)
    try:
        item["settings"] = json.loads(item.pop("settings_json") or "{}")
    except Exception:
        item["settings"] = {}
    return item


def list_report_configurations(db, report_type: str, start_person_id: int):
    ensure_report_configuration_schema(db)
    rows = db.execute(
        """
        SELECT *
        FROM companion_report_configurations
        WHERE report_type=? AND start_person_id=?
        ORDER BY lower(name), id
        """,
        (str(report_type), int(start_person_id)),
    ).fetchall()
    return [_decode(row) for row in rows]


def get_report_configuration(db, config_id: int, *, report_type: str | None = None, start_person_id: int | None = None):
    ensure_report_configuration_schema(db)
    sql = "SELECT * FROM companion_report_configurations WHERE id=?"
    args = [int(config_id)]
    if report_type is not None:
        sql += " AND report_type=?"
        args.append(str(report_type))
    if start_person_id is not None:
        sql += " AND start_person_id=?"
        args.append(int(start_person_id))
    return _decode(db.execute(sql, args).fetchone())


def save_report_configuration(
    db,
    report_type: str,
    start_person_id: int,
    name: str,
    settings: dict,
    *,
    config_id: int | None = None,
):
    ensure_report_configuration_schema(db)
    clean_name = " ".join(str(name or "").split()).strip()
    if not clean_name:
        raise ValueError("Report configuration name is required.")
    stamp = _utcnow()
    payload = json.dumps(settings or {}, sort_keys=True, separators=(",", ":"))

    if config_id is None:
        existing = db.execute(
            """
            SELECT id FROM companion_report_configurations
            WHERE report_type=? AND start_person_id=? AND name=? COLLATE NOCASE
            """,
            (str(report_type), int(start_person_id), clean_name),
        ).fetchone()
        if existing:
            raise ValueError(f"A report configuration named '{clean_name}' already exists. Load it to update it.")
        cur = db.execute(
            """
            INSERT INTO companion_report_configurations(
                report_type,start_person_id,name,settings_json,created_at,updated_at
            ) VALUES(?,?,?,?,?,?)
            """,
            (str(report_type), int(start_person_id), clean_name, payload, stamp, stamp),
        )
        db.commit()
        return int(cur.lastrowid)

    current = get_report_configuration(
        db,
        int(config_id),
        report_type=str(report_type),
        start_person_id=int(start_person_id),
    )
    if current is None:
        raise ValueError("The selected report configuration no longer exists.")
    clash = db.execute(
        """
        SELECT id FROM companion_report_configurations
        WHERE report_type=? AND start_person_id=? AND name=? COLLATE NOCASE AND id<>?
        """,
        (str(report_type), int(start_person_id), clean_name, int(config_id)),
    ).fetchone()
    if clash:
        raise ValueError(f"A report configuration named '{clean_name}' already exists.")
    db.execute(
        """
        UPDATE companion_report_configurations
        SET name=?, settings_json=?, updated_at=?
        WHERE id=?
        """,
        (clean_name, payload, stamp, int(config_id)),
    )
    db.commit()
    return int(config_id)


def delete_report_configuration(db, config_id: int, *, report_type: str | None = None, start_person_id: int | None = None) -> bool:
    ensure_report_configuration_schema(db)
    sql = "DELETE FROM companion_report_configurations WHERE id=?"
    args = [int(config_id)]
    if report_type is not None:
        sql += " AND report_type=?"
        args.append(str(report_type))
    if start_person_id is not None:
        sql += " AND start_person_id=?"
        args.append(int(start_person_id))
    cur = db.execute(sql, args)
    db.commit()
    return bool(cur.rowcount)
