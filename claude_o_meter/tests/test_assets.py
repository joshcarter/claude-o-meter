"""Asset loading: the cluster background and the three display fonts (TD-2)."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from claude_o_meter import assets, layout  # noqa: E402


def test_background_loads_at_screen_size():
    pygame.init()
    try:
        bg = assets.load_image(layout.BACKGROUND)
        assert bg.get_size() == (layout.SCREEN_W, layout.SCREEN_H)
    finally:
        pygame.quit()


def test_fonts_load_and_render():
    pygame.init()
    try:
        for name, size in [
            (layout.FONT_READOUT, layout.READOUT_SIZE),
            (layout.FONT_MONEY, layout.MONEY_SIZE),
            (layout.FONT_LABEL, layout.LABEL_SIZE),
        ]:
            font = assets.load_font(name, size)
            surf = font.render("88", True, layout.C_LIGHT)
            assert surf.get_width() > 0 and surf.get_height() > 0
    finally:
        pygame.quit()


def test_each_font_file_has_a_license_alongside():
    # OFL compliance guard: the font files we ship must keep their license.
    for lic in ("DSEG-LICENSE.txt", "RobotoCondensed-OFL.txt"):
        assert os.path.exists(assets.font_path(lic))
