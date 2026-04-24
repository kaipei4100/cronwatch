"""Persistent store for job heartbeat timestamps (SQLite-backed)."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

DEFAULT_DB_PATH = Path("cronwatch.db")

DDL = """
CREATE TABLE IF NOT EXISTS heartbeats (
    job_name  TEXT PRIMARY KEY,
    last_seen TEXT NOT NULL,
    run_count INTEGER NOT NULL DEFAULT 0
);
"""


class HeartbeatStore:
    """Read/write job heartbeat records."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def _init_db(self) -> None:
        with self._conn() as con:
            con.executescript(DDL)

    def record(self, job_name: str, ts: Optional[datetime] = None) -> None:
        """Record a heartbeat for *job_name* at *ts* (default: utcnow)."""
        ts = ts or datetime.utcnow()
        with self._conn() as con:
            con.execute(
                """
                INSERT INTO heartbeats (job_name, last_seen, run_count)
                VALUES (?, ?, 1)
                ON CONFLICT(job_name) DO UPDATE SET
                    last_seen = excluded.last_seen,
                    run_count = run_count + 1
                """,
                (job_name, ts.isoformat()),
            )

    def last_seen(self, job_name: str) -> Optional[datetime]:
        """Return the last heartbeat datetime for *job_name*, or None."""
        with self._conn() as con:
            row = con.execute(
                "SELECT last_seen FROM heartbeats WHERE job_name = ?", (job_name,)
            ).fetchone()
        if row is None:
            return None
        return datetime.fromisoformat(row["last_seen"])

    def all_records(self) -> dict[str, datetime]:
        """Return a mapping of job_name -> last_seen for all tracked jobs."""
        with self._conn() as con:
            rows = con.execute("SELECT job_name, last_seen FROM heartbeats").fetchall()
        return {r["job_name"]: datetime.fromisoformat(r["last_seen"]) for r in rows}
