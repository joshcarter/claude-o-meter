import asyncio
import logging
import os
import threading
import time

from .config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
log = logging.getLogger(__name__)


def _start_poll_thread(coro_factory):
    """Run an async coroutine on a background daemon thread with its own event loop."""
    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro_factory())
        except Exception as exc:
            log.error("Poll thread crashed: %s", exc)
        finally:
            loop.close()

    t = threading.Thread(target=_run, daemon=True, name="poll")
    t.start()
    return t


def main():
    from . import state

    cfg = load_config()
    log.info("Starting claude-o-meter (source=%s)", cfg.data_source)

    if cfg.data_source == "live":
        from .store import Store
        from .poller import polling_loop

        os.environ.setdefault("POLL_INTERVAL_SECONDS", str(cfg.poll_seconds))
        db_path = os.environ.get("DB_PATH", "./samples.db")
        store = Store(db_path)
        _start_poll_thread(lambda: polling_loop(store))

    elif cfg.data_source == "fake":
        from .fakesource import fake_loop
        _start_poll_thread(lambda: fake_loop(cfg.poll_seconds))

    else:
        raise ValueError(f"Unknown DATA_SOURCE: {cfg.data_source!r}")

    # Main thread: log snapshot once/second (placeholder for the pygame loop in TD-3)
    while True:
        s = state.snapshot
        log.info(
            "snapshot: 5h=%.1f%% redline=%s  7d=%.1f%% redline=%s  stale=%s",
            s.five_hour_pct or 0.0,
            f"{s.five_hour_redline_ratio:.2f}" if s.five_hour_redline_ratio is not None else "n/a",
            s.seven_day_pct or 0.0,
            f"{s.seven_day_redline_ratio:.2f}" if s.seven_day_redline_ratio is not None else "n/a",
            s.stale,
        )
        time.sleep(1)
