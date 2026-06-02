import asyncio
import logging
import os
import threading

from . import layout
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


def _start_poll_source(cfg):
    """Start the configured data source on the background poll thread."""
    if cfg.data_source == "live":
        from .store import Store
        from .poller import polling_loop

        os.environ.setdefault("POLL_INTERVAL_SECONDS", str(cfg.poll_seconds))
        db_path = os.environ.get("DB_PATH", "./samples.db")
        store = Store(db_path)
        return _start_poll_thread(lambda: polling_loop(store))

    if cfg.data_source == "fake":
        from .fakesource import fake_loop
        # The fake source ticks on its own fast interval (not the poll cadence)
        # so the desktop demo animates smoothly.
        return _start_poll_thread(fake_loop)

    raise ValueError(f"Unknown DATA_SOURCE: {cfg.data_source!r}")


def run_display(cfg, max_frames=None):
    """Open a 480×320 surface and run the pygame loop on the calling (main)
    thread, rendering ``state.snapshot`` each frame.

    ``max_frames`` bounds the loop for headless verification/tests; ``None``
    runs until the window is closed. Honours ``SDL_VIDEODRIVER=dummy`` for
    headless runs (no window, no display required).

    With ``DISPLAY_MODE = "framebuffer"`` (the Pi PiTFT) the surface is rendered
    offscreen via the SDL ``dummy`` driver and copied to ``cfg.fb_device`` each
    frame — no X server or window required on Raspberry Pi OS Lite.
    """
    framebuffer_mode = cfg.display_mode == "framebuffer"
    if framebuffer_mode:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    import pygame

    from . import render, state

    pygame.init()
    fb = None
    try:
        surface = pygame.display.set_mode((layout.SCREEN_W, layout.SCREEN_H))
        pygame.display.set_caption("claude-o-meter")
        if framebuffer_mode:
            from .framebuffer import Framebuffer

            fb = Framebuffer(cfg.fb_device, layout.SCREEN_W, layout.SCREEN_H)
            log.info("Rendering to framebuffer %s", cfg.fb_device)
        clock = pygame.time.Clock()

        frames = 0
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            render.render_frame(surface, state.snapshot, cfg)
            if fb is not None:
                fb.blit(surface)
            else:
                pygame.display.flip()
            clock.tick(layout.FPS)

            frames += 1
            if max_frames is not None and frames >= max_frames:
                running = False
        return frames
    finally:
        if fb is not None:
            fb.close()
        pygame.quit()


def main():
    cfg = load_config()
    log.info("Starting claude-o-meter (source=%s)", cfg.data_source)
    _start_poll_source(cfg)
    run_display(cfg)
