from __future__ import annotations

import sqlite3
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class NotificationDeviceStore:
    def __init__(self, database_path: str) -> None:
        self.database_path = Path(database_path)

    def register(
        self,
        *,
        installation_id: str,
        fcm_token: str,
        platform: str,
        device_name: str | None,
    ) -> dict[str, Any]:
        self._initialize()
        with self._connection() as connection:
            connection.execute(
                "DELETE FROM notification_devices "
                "WHERE fcm_token = ? AND installation_id != ?",
                (fcm_token, installation_id),
            )
            connection.execute(
                """
                INSERT INTO notification_devices (
                    installation_id,
                    fcm_token,
                    platform,
                    device_name
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(installation_id) DO UPDATE SET
                    fcm_token = excluded.fcm_token,
                    platform = excluded.platform,
                    device_name = excluded.device_name,
                    enabled = 1,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (installation_id, fcm_token, platform, device_name),
            )
            row = connection.execute(
                """
                SELECT installation_id, platform, device_name, enabled,
                       created_at, updated_at
                FROM notification_devices
                WHERE installation_id = ?
                """,
                (installation_id,),
            ).fetchone()

        if row is None:
            raise RuntimeError("Registered notification device was not found")
        return dict(row)

    def count_enabled(self) -> int:
        self._initialize()
        with self._connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM notification_devices WHERE enabled = 1"
            ).fetchone()
        return int(row["count"])

    def enabled_devices(self) -> list[dict[str, Any]]:
        self._initialize()
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT installation_id, fcm_token
                FROM notification_devices
                WHERE enabled = 1
                ORDER BY created_at
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def disable_device(self, installation_id: str) -> None:
        self._initialize()
        with self._connection() as connection:
            connection.execute(
                """
                UPDATE notification_devices
                SET enabled = 0, updated_at = CURRENT_TIMESTAMP
                WHERE installation_id = ?
                """,
                (installation_id,),
            )

    def create_round(self, *, scheduled_at: str, source: str) -> dict[str, Any]:
        self._initialize()
        with self._connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO rounds (scheduled_at, source)
                VALUES (?, ?)
                """,
                (scheduled_at, source),
            )
            row = connection.execute(
                "SELECT * FROM rounds WHERE scheduled_at = ?",
                (scheduled_at,),
            ).fetchone()
        if row is None:
            raise RuntimeError("Round could not be created")
        return dict(row)

    def set_round_status(
        self,
        round_id: int,
        status: str,
        *,
        result: str | None = None,
        confidence: float | None = None,
        error: str | None = None,
    ) -> None:
        self._initialize()
        with self._connection() as connection:
            connection.execute(
                """
                UPDATE rounds
                SET status = ?, result = ?, confidence = ?, error = ?,
                    started_at = CASE
                        WHEN ? = 'running' THEN CURRENT_TIMESTAMP
                        ELSE started_at
                    END,
                    completed_at = CASE
                        WHEN ? IN ('completed', 'failed', 'skipped')
                        THEN CURRENT_TIMESTAMP
                        ELSE completed_at
                    END
                WHERE id = ?
                """,
                (status, result, confidence, error, status, status, round_id),
            )

    def add_classification(
        self,
        *,
        round_id: int,
        sample_index: int,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        self._initialize()
        result = result or {}
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO round_classifications (
                    round_id, sample_index, predicted_class, confidence,
                    frame_id, raw_json, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    round_id,
                    sample_index,
                    result.get("predicted_class"),
                    result.get("confidence"),
                    str(result["frame_id"]) if result.get("frame_id") is not None else None,
                    json.dumps(result, separators=(",", ":")) if result else None,
                    error,
                ),
            )

    def list_rounds(self, limit: int = 20) -> list[dict[str, Any]]:
        self._initialize()
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT r.*,
                       COUNT(c.id) AS sample_count,
                       SUM(CASE WHEN c.id IS NOT NULL AND c.error IS NULL THEN 1 ELSE 0 END) AS valid_sample_count
                FROM rounds r
                LEFT JOIN round_classifications c ON c.round_id = r.id
                GROUP BY r.id
                ORDER BY r.scheduled_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_round(self, round_id: int) -> dict[str, Any] | None:
        self._initialize()
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM rounds WHERE id = ?", (round_id,)
            ).fetchone()
            if row is None:
                return None
            classifications = connection.execute(
                """
                SELECT sample_index, predicted_class, confidence, frame_id, error,
                       created_at
                FROM round_classifications
                WHERE round_id = ?
                ORDER BY sample_index
                """,
                (round_id,),
            ).fetchall()
        result = dict(row)
        result["classifications"] = [dict(item) for item in classifications]
        return result

    def record_delivery(
        self,
        *,
        round_id: int | None,
        installation_id: str,
        notification_type: str,
        status: str,
        message_id: str | None = None,
        error: str | None = None,
    ) -> None:
        self._initialize()
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO notification_deliveries (
                    round_id, installation_id, notification_type, status,
                    message_id, error
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    round_id,
                    installation_id,
                    notification_type,
                    status,
                    message_id,
                    error,
                ),
            )

    def reset_interrupted_round(self, round_id: int) -> None:
        self._initialize()
        with self._connection() as connection:
            connection.execute(
                "DELETE FROM round_classifications WHERE round_id = ?",
                (round_id,),
            )
            connection.execute(
                """
                UPDATE rounds
                SET status = 'pending', result = NULL, confidence = NULL,
                    error = NULL, started_at = NULL, completed_at = NULL
                WHERE id = ? AND status = 'running'
                """,
                (round_id,),
            )

    def _initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS notification_devices (
                    installation_id TEXT PRIMARY KEY,
                    fcm_token TEXT UNIQUE NOT NULL,
                    platform TEXT NOT NULL CHECK (platform = 'android'),
                    device_name TEXT,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS rounds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scheduled_at TEXT UNIQUE NOT NULL,
                    source TEXT NOT NULL CHECK (source IN ('automatic', 'debug')),
                    status TEXT NOT NULL DEFAULT 'pending',
                    result TEXT,
                    confidence REAL,
                    error TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS round_classifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    round_id INTEGER NOT NULL REFERENCES rounds(id) ON DELETE CASCADE,
                    sample_index INTEGER NOT NULL,
                    predicted_class TEXT,
                    confidence REAL,
                    frame_id TEXT,
                    raw_json TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(round_id, sample_index)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS notification_deliveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    round_id INTEGER REFERENCES rounds(id) ON DELETE SET NULL,
                    installation_id TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message_id TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()
