"""
settings_repository.py — SQLite-backed settings and alert-history persistence.
"""
from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS: Dict[str, Any] = {
    "disk_warning": 80.0,
    "disk_critical": 90.0,
    "ram_warning": 80.0,
    "ram_critical": 90.0,
    "swap_warning": 70.0,
    "swap_critical": 90.0,
    "cpu_warning": 80.0,
    "cpu_critical": 95.0,
    "sound_enabled": True,
    "monitor_interval": 2,      # seconds
    "max_scan_entries": 10000,
    "default_scan_path": str(Path.home()),
    "detect_duplicates": False,
    "follow_symlinks": False,
    "min_file_size_mb": 0,
}

_DB_PATH = Path.home() / ".config" / "ubuntu-storage-analyzer" / "settings.db"


class SettingsRepository:
    def __init__(self, db_path: Optional[Path] = None):
        self._path = db_path or _DB_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._init_db()

    def _init_db(self) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                resource TEXT NOT NULL,
                level TEXT NOT NULL,
                value REAL NOT NULL,
                message TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

        # Seed defaults if missing
        for key, val in DEFAULT_SETTINGS.items():
            cur.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, json.dumps(val)),
            )
        self._conn.commit()

    # ── Settings ──────────────────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        cur = self._conn.cursor()
        row = cur.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        if row is None:
            return default
        return json.loads(row[0])

    def set(self, key: str, value: Any) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, json.dumps(value)),
        )
        self._conn.commit()

    def all_settings(self) -> Dict[str, Any]:
        cur = self._conn.cursor()
        rows = cur.execute("SELECT key, value FROM settings").fetchall()
        return {k: json.loads(v) for k, v in rows}

    def reset_defaults(self) -> None:
        for key, val in DEFAULT_SETTINGS.items():
            self.set(key, val)

    # ── Alert History ─────────────────────────────────────────────────────────

    def save_alert(self, timestamp: float, resource: str, level: str, value: float, message: str) -> None:
        self._conn.execute(
            "INSERT INTO alert_history (timestamp, resource, level, value, message) VALUES (?,?,?,?,?)",
            (timestamp, resource, level, value, message),
        )
        self._conn.commit()

    def get_alerts(self, limit: int = 500) -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        rows = cur.execute(
            "SELECT timestamp, resource, level, value, message FROM alert_history ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {"timestamp": r[0], "resource": r[1], "level": r[2], "value": r[3], "message": r[4]}
            for r in rows
        ]

    def clear_alert_history(self) -> None:
        self._conn.execute("DELETE FROM alert_history")
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
