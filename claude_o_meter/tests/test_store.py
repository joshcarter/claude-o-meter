"""Store persistence + SD-card-wear settings.

The Pi writes samples to an SD card, so these tests pin the choices that keep
that gentle: one reused connection (not a fresh open per call) and WAL +
synchronous=NORMAL so commits don't fsync. A regression back to per-call
``sqlite3.connect()`` or rollback-journal mode should fail here.
"""

from claude_o_meter.store import Store


def test_uses_wal_and_relaxed_sync(tmp_path):
    store = Store(str(tmp_path / "samples.db"))
    try:
        mode = store._conn.execute("PRAGMA journal_mode").fetchone()[0]
        sync = store._conn.execute("PRAGMA synchronous").fetchone()[0]
        assert mode.lower() == "wal"
        assert sync == 1  # NORMAL
    finally:
        store.close()


def test_connection_is_reused_across_calls(tmp_path):
    store = Store(str(tmp_path / "samples.db"))
    try:
        before = store._conn
        store.insert(1000, 10.0, 20.0, None)
        store.recent_five_hour(0)
        store.prune(0)
        store.hourly_peaks(3)
        assert store._conn is before  # never reopened
    finally:
        store.close()


def test_data_survives_across_store_instances(tmp_path):
    db = str(tmp_path / "samples.db")
    s1 = Store(db)
    s1.insert(1000, 10.0, 20.0, 5.0)
    s1.close()

    s2 = Store(db)
    try:
        assert s2.recent_five_hour(0) == [(1000, 10.0)]
    finally:
        s2.close()


def test_recreates_on_corrupt_db(tmp_path):
    db = tmp_path / "samples.db"
    db.write_bytes(b"this is not a sqlite database")  # garbage header
    store = Store(str(db))  # must not raise — recreate path kicks in
    try:
        store.insert(1000, 10.0, 20.0, None)
        assert store.recent_five_hour(0) == [(1000, 10.0)]
    finally:
        store.close()
