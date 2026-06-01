"""Shared test fixtures."""

import pytest


@pytest.fixture(autouse=True)
def _reset_render_caches():
    """Drop render's cached SDL resources after each test. The tests cycle
    pygame.init()/pygame.quit(); a font or surface cached under one pygame
    lifecycle must not be reused after quit() (stale native handle → crash)."""
    yield
    from claude_o_meter import render
    render.reset_caches()
