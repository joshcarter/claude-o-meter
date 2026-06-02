import sqlite3
import time
from pathlib import Path
from typing import Optional

_SCHEMA = """
CREATE TABLE IF NOT EXISTS samples (
    ts              INTEGER NOT NULL,
    five_hour       REAL,
    seven_day       REAL,
    seven_day_opus  REAL
);
CREATE INDEX IF NOT EXISTS samples_ts ON samples(ts);
"""


class Store:
    """Sample history backed by one long-lived SQLite connection.

    On the Pi the DB lives on the SD card, so writes are a wear source. Two
    choices keep that gentle:

    * **One persistent connection**, opened once and reused. The old code opened
      a fresh ``sqlite3.connect()`` for every call — 4+ file-open/WAL-probe
      cycles per 60s poll, each real SD I/O.
    * **WAL + ``synchronous=NORMAL``**: a COMMIT no longer fsyncs; only the
      periodic WAL checkpoint touches the disk, rolling many samples into a
      single write. A power cut can lose the last few un-checkpointed samples
      but never corrupts the DB — and the data is regenerable monitoring history,
      so that trade is right.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = self._open()

    def _connect(self) -> sqlite3.Connection:
        # check_same_thread=False: the connection is created on the main thread
        # (Store is built in main._start_poll_source) but used from the single
        # poll thread. Access is serialized — one poll at a time, and the main
        # thread is done with it before the poll thread starts — so no locking
        # is needed.
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _open(self) -> sqlite3.Connection:
        import logging
        try:
            conn = self._connect()
            with conn:
                conn.executescript(_SCHEMA)
            return conn
        except Exception as exc:
            logging.error("DB init failed, recreating: %s", exc)
            # Drop the main DB and its WAL/SHM sidecars so the recreate starts clean.
            for suffix in ("", "-wal", "-shm"):
                Path(self.db_path + suffix).unlink(missing_ok=True)
            conn = self._connect()
            with conn:
                conn.executescript(_SCHEMA)
            return conn

    def insert(
        self,
        ts: int,
        five_hour: float,
        seven_day: float,
        seven_day_opus: Optional[float],
    ) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO samples VALUES (?, ?, ?, ?)",
                (ts, five_hour, seven_day, seven_day_opus),
            )

    def recent_five_hour(self, since_ts: int) -> list[tuple[int, float]]:
        return self._conn.execute(
            "SELECT ts, five_hour FROM samples WHERE ts >= ? AND five_hour IS NOT NULL ORDER BY ts",
            (since_ts,),
        ).fetchall()

    def recent_seven_day(self, since_ts: int) -> list[tuple[int, float]]:
        return self._conn.execute(
            "SELECT ts, seven_day FROM samples WHERE ts >= ? AND seven_day IS NOT NULL ORDER BY ts",
            (since_ts,),
        ).fetchall()

    def hourly_peaks(self, hours: int) -> list[dict]:
        now = int(time.time())
        # align to start of current UTC hour
        hour_start = (now // 3600) * 3600
        start_ts = hour_start - (hours - 1) * 3600

        rows = self._conn.execute(
            """
            SELECT (ts / 3600) * 3600 AS h, MAX(five_hour)
            FROM samples
            WHERE ts >= ? AND five_hour IS NOT NULL
            GROUP BY h
            ORDER BY h
            """,
            (start_ts,),
        ).fetchall()

        peaks = {row[0]: row[1] for row in rows}
        return [
            {"hour_unix": start_ts + i * 3600, "five_hour_peak": peaks.get(start_ts + i * 3600)}
            for i in range(hours)
        ]

    def prune(self, older_than_ts: int) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM samples WHERE ts < ?", (older_than_ts,))

    def close(self) -> None:
        self._conn.close()
