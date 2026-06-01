"""Manual visual check: reveal the tach bars one by one, then the fuel bars.

Opens a real 480×320 window (needs a desktop display — this is not an automated
test). Run it from the repo root:

    python -m claude_o_meter.demo_reveal           # default 150 ms/step
    python -m claude_o_meter.demo_reveal 300        # slower

Close the window or press Esc/Q to quit early.
"""

import sys

import pygame

from . import layout, render
from .config import load_config


def _draw(surface, cfg, tach_lit, fuel_lit):
    surface.fill(layout.C_BG)
    surface.blit(render._get_background(), (0, 0))
    render.dim_tach(surface, tach_lit, cfg.dim_opacity)
    render.dim_fuel(surface, fuel_lit, cfg.dim_opacity)
    pygame.display.flip()


def _wants_quit():
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            return True
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_q):
            return True
    return False


def main(delay_ms=150):
    cfg = load_config()
    pygame.init()
    surface = pygame.display.set_mode((layout.SCREEN_W, layout.SCREEN_H))
    pygame.display.set_caption("claude-o-meter — reveal demo")
    try:
        # Start fully dimmed.
        _draw(surface, cfg, 0, 0)
        pygame.time.delay(delay_ms * 3)

        # Reveal the tach bars one at a time (fuel stays empty).
        for lit in range(1, layout.TACH_SEGMENTS + 1):
            if _wants_quit():
                return
            _draw(surface, cfg, lit, 0)
            pygame.time.delay(delay_ms)
        pygame.time.delay(delay_ms * 2)

        # Reveal the fuel bars one at a time (tach stays full).
        for lit in range(1, layout.FUEL_SEGMENTS + 1):
            if _wants_quit():
                return
            _draw(surface, cfg, layout.TACH_SEGMENTS, lit)
            pygame.time.delay(delay_ms)

        # Hold the final frame until the window is closed.
        while not _wants_quit():
            pygame.time.delay(50)
    finally:
        pygame.quit()


if __name__ == "__main__":
    delay = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    main(delay)
