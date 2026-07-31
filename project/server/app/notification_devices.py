from __future__ import annotations

import sqlite3
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

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()
