"""Framebuffer pixel packing (TD-4.3).

``Framebuffer._to_bytes`` is the one piece of the PiTFT path that can be wrong
in a way nothing else catches: a swapped transpose axis or an off-by-one bit
shift produces a rotated or mis-coloured panel that looks fine in CI (no panel)
and is near-impossible to debug remotely on the Pi. These tests pin both the
RGB565 channel packing and the (W,H)→(H,W) transpose using the SDL ``dummy``
driver — no ``/dev/fb`` and no display required.

``_to_bytes`` only touches ``self.bpp``, so we build the instance with
``object.__new__`` and skip the hardware ``__init__``.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import numpy as np  # noqa: E402
import pygame  # noqa: E402

from claude_o_meter.framebuffer import Framebuffer  # noqa: E402

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)

# Standard RGB565 for each primary at full intensity.
RGB565_RED = 0xF800     # 0b11111_000000_00000
RGB565_GREEN = 0x07E0   # 0b00000_111111_00000
RGB565_BLUE = 0x001F    # 0b00000_000000_11111
RGB565_WHITE = 0xFFFF


def _fb(bpp):
    fb = object.__new__(Framebuffer)  # skip the /dev/fb hardware __init__
    fb.bpp = bpp
    return fb


def test_to_bytes_rgb565_channel_packing():
    """Each primary packs to the canonical RGB565 word, little-endian."""
    pygame.init()
    try:
        for color, expected in [
            (RED, RGB565_RED),
            (GREEN, RGB565_GREEN),
            (BLUE, RGB565_BLUE),
            (WHITE, RGB565_WHITE),
        ]:
            surf = pygame.Surface((4, 4))
            surf.fill(color)
            words = np.frombuffer(_fb(16)._to_bytes(surf), dtype="<u2")
            assert set(words.tolist()) == {expected}, f"{color} → {words[0]:#06x}"
    finally:
        pygame.quit()


def test_to_bytes_transpose_orientation():
    """Output is row-major (H,W): the byte sequence walks rows top-to-bottom,
    columns left-to-right. A wrong transpose axis would scramble this — e.g.
    swap the green/blue positions below."""
    pygame.init()
    try:
        surf = pygame.Surface((2, 2))
        surf.set_at((0, 0), RED)      # col 0, row 0
        surf.set_at((1, 0), GREEN)    # col 1, row 0
        surf.set_at((0, 1), BLUE)     # col 0, row 1
        surf.set_at((1, 1), WHITE)    # col 1, row 1

        words = np.frombuffer(_fb(16)._to_bytes(surf), dtype="<u2")
        assert words.tolist() == [
            RGB565_RED, RGB565_GREEN,    # row 0
            RGB565_BLUE, RGB565_WHITE,   # row 1
        ]
    finally:
        pygame.quit()


def test_to_bytes_32bpp_is_bgra():
    """The 32bpp fallback hands the panel B,G,R,X byte order."""
    pygame.init()
    try:
        surf = pygame.Surface((1, 1))
        surf.fill(RED)
        buf = _fb(32)._to_bytes(surf)
        assert buf[:3] == bytes((0, 0, 255))  # B=0, G=0, R=255
    finally:
        pygame.quit()
