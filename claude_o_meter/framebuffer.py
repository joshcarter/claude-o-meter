"""Direct-to-framebuffer output for the Pi PiTFT (TD-4.3).

The 3.5" PiTFT is driven by the legacy ``fb_hx8357d`` fbtft framebuffer driver
(the ``pitft35-resistive`` overlay *without* the ``,drm`` flag — the DRM variant
leaves the panel's display pipe off until a modeset, so writes never appear).
That driver exposes ``/dev/fb1`` as a plain framebuffer that flushes to the
panel on write: 480×320, **16 bpp RGB565**, stride 960.

We render the pygame surface offscreen (SDL ``dummy`` driver — no X needed on
Lite) and copy it into the framebuffer each frame, packing to RGB565. A 32bpp
``BGRA`` path is kept as a fallback in case the panel is ever brought up under
the 32bpp DRM driver instead.
"""

import mmap
import os

import pygame

try:
    import numpy as np
except ImportError:  # pragma: no cover - exercised only on a 16bpp panel
    np = None


def _sysfs_int(fb_index: int, attr: str, default: int) -> int:
    try:
        with open(f"/sys/class/graphics/fb{fb_index}/{attr}") as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return default


class Framebuffer:
    """An mmap'd Linux framebuffer the renderer copies finished frames into."""

    def __init__(self, device: str = "/dev/fb1", width: int = 480, height: int = 320):
        self.device = device
        self.width = width
        self.height = height

        fb_index = int("".join(c for c in os.path.basename(device) if c.isdigit()) or "1")
        self.bpp = _sysfs_int(fb_index, "bits_per_pixel", 16)
        if self.bpp not in (16, 32):
            raise RuntimeError(f"{device}: unsupported bits_per_pixel={self.bpp}")
        self.bytes_per_pixel = self.bpp // 8

        # stride (line length in bytes) can exceed width*bpp if the driver pads
        # rows; for this panel it's exactly width*bpp (no padding), but read it
        # so a padded panel still renders correctly.
        self.stride = _sysfs_int(fb_index, "stride", width * self.bytes_per_pixel)
        self._row_bytes = width * self.bytes_per_pixel
        self._map_size = self.stride * height

        if self.bpp == 16 and np is None:
            raise RuntimeError(
                "16bpp framebuffer needs numpy for RGB565 packing — pip install numpy"
            )

        self._fd = os.open(device, os.O_RDWR)
        self._mm = mmap.mmap(
            self._fd, self._map_size, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE
        )

    def _to_bytes(self, surface: "pygame.Surface") -> bytes:
        if self.bpp == 32:
            # Panel byte order B,G,R,X → pygame "BGRA" matches it.
            return pygame.image.tostring(surface, "BGRA")
        # 16bpp RGB565, little-endian. surfarray gives (W, H, 3) in RGB; move to
        # (H, W) row-major and pack the channels.
        arr = pygame.surfarray.array3d(surface).transpose(1, 0, 2)
        r = arr[:, :, 0].astype(np.uint16)
        g = arr[:, :, 1].astype(np.uint16)
        b = arr[:, :, 2].astype(np.uint16)
        rgb565 = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
        return rgb565.astype("<u2").tobytes()

    def blit(self, surface: "pygame.Surface") -> None:
        """Copy a 480×320 pygame surface to the panel."""
        buf = self._to_bytes(surface)
        if self.stride == self._row_bytes:
            self._mm[: len(buf)] = buf  # contiguous: one bulk copy
        else:
            # Padded rows: copy row by row into the wider stride.
            for y in range(self.height):
                src = y * self._row_bytes
                dst = y * self.stride
                self._mm[dst : dst + self._row_bytes] = buf[src : src + self._row_bytes]
        self._mm.flush()  # msync: nudge fbtft's deferred-IO to push over SPI

    def close(self) -> None:
        try:
            self._mm.close()
        finally:
            os.close(self._fd)
