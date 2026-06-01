"""Asset resolution and loading (images + fonts) for the renderer.

Assets live in ``claude_o_meter/assets/`` (images) and
``claude_o_meter/assets/fonts/`` (TTFs). Paths are resolved relative to this
module so the package works from a source checkout, an editable install, or a
venv on the Pi.

pygame.font must be initialised (``pygame.init()`` covers it) before
``load_font`` is called.
"""

import os

import pygame

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
_FONTS_DIR = os.path.join(_ASSETS_DIR, "fonts")


def asset_path(*parts):
    """Absolute path to an asset under ``assets/``."""
    return os.path.join(_ASSETS_DIR, *parts)


def font_path(filename):
    """Absolute path to a font under ``assets/fonts/``."""
    return os.path.join(_FONTS_DIR, filename)


def load_image(filename):
    """Load an image from ``assets/``. Converts to the display format when a
    display surface exists (faster blits); loads raw otherwise (headless)."""
    img = pygame.image.load(asset_path(filename))
    if pygame.display.get_surface() is not None:
        img = img.convert()
    return img


def load_font(filename, size):
    """Load a TTF from ``assets/fonts/`` at ``size`` px."""
    return pygame.font.Font(font_path(filename), size)
