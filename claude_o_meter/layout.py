"""Named layout constants for the 480×320 instrument cluster.

Exact pixel locations, segment-boundary coordinates and font sizes are still
pending the art spec (see TODO.md "Pending user input"). Everything here is a
**named, provisional** value so the renderer can be built and run now and the
real numbers can drop in later without restructuring the code that references
them.

Colours are carried over from the PyPortal ``code.py`` palette.
"""

# --- Surface ----------------------------------------------------------------
SCREEN_W = 480
SCREEN_H = 320
FPS = 30

# --- Assets (under assets/ — see assets/fonts/README.md) --------------------
# The all-segments-lit cluster bitmap that the dim rectangles darken.
BACKGROUND = "background.png"

# Fonts (in assets/fonts/). Files chosen per the cluster design. The non-Mini
# DSEG7 Modern faces are kept in assets/fonts/ as alternates.
FONT_READOUT = "DSEG7ModernMini-Italic.ttf"        # 0–99 tach readout
FONT_MONEY = "DSEG7ModernMini-BoldItalic.ttf"      # dollar amounts + reset date/time
FONT_LABEL = "RobotoCondensed-BoldItalic.ttf"      # labels / messages

# Point sizes (art is 72 DPI → 1 pt = 1 px). MONEY/LABEL still provisional.
READOUT_SIZE = 80
MONEY_SIZE = 22
LABEL_SIZE = 16

# Dimming-rectangle default opacity (0–255). 212 ≈ 83%, matches the PyPortal
# ghost. config.toml's DIM_OPACITY overrides this per-deployment at the call site.
DIM_DEFAULT_OPACITY = 212

# --- Colours (RGB) — from code.py C_* palette -------------------------------
C_BG = (0x00, 0x00, 0x00)      # background
C_DARK = (0x0B, 0x1D, 0x20)    # unlit "ghost" segments
C_LIGHT = (0x40, 0xA9, 0xBF)   # lit segments / live readouts
C_ERROR = (0xFF, 0x22, 0x00)   # fault text

# --- 20-segment tach bar (right-pinned dim) ---------------------------------
# The arc's bars are revealed left→right by a tall dim rectangle that spans the
# full arc height (TACH_DIM_TOP..TACH_DIM_BOTTOM) and slides horizontally. Its
# left edge sits at TACH_DIM_LEFT0 when fully dimmed (0 lit) and advances right
# by TACH_PITCH per revealed segment; the right/top/bottom edges are fixed.
# Driven by 5h redline_ratio via gauges.tach_position().
TACH_SEGMENTS = 20
TACH_DIM_LEFT0 = 10     # dim left edge with 0 segments lit
TACH_PITCH = 20         # px the left edge advances per lit segment
TACH_DIM_TOP = 16
TACH_DIM_RIGHT = 403
TACH_DIM_BOTTOM = 286

# --- Two-digit 0–99 readout (numeric form of the tach) ----------------------
# DSEG7 Modern Mini Italic. Drawn as a dim "88" ghost (all segments) with the
# live value bright over it. NUM_POS is the top-left of the visible "88".
NUM_POS = (190, 172)

# --- Vertical 20-segment fuel gauge (top-pinned dim) ------------------------
# remaining = clamp(100 − seven_day.utilization, 0, 100), linear. Lit segments
# fill bottom→top; the dim rectangle is pinned at the top (FUEL_DIM_TOP) and its
# bottom edge retreats upward as fuel is revealed: bottom edge at
# FUEL_DIM_BOTTOM0 when fully dimmed (0 lit), rising by FUEL_PITCH per segment.
FUEL_SEGMENTS = 20
FUEL_DIM_BOTTOM0 = 220  # dim bottom edge with 0 segments lit
FUEL_PITCH = 8          # px the bottom edge retreats per lit segment
FUEL_DIM_LEFT = 422
FUEL_DIM_RIGHT = 456
FUEL_DIM_TOP = 63

# --- Warning lights (dimmed when OFF; lit = condition true) -----------------
# Rects are (x, y, w, h). The check-engine light sits under the tach arc, so the
# tach dim always excludes CHECK_ENGINE_RECT and the light is dimmed solely by
# its own rect — otherwise the overlap would dim it twice (too dark).
CHECK_ENGINE_RECT = (355, 232, 48, 46)   # (355,232)–(403,278)
LOW_FUEL_RECT = (416, 232, 48, 46)       # (416,232)–(464,278); clear of the tach

# --- Money + reset readouts -------------------------------------------------
EXTRA_USE_X = 24
EXTRA_USE_Y = 220
EXTRA_LIMIT_X = 24
EXTRA_LIMIT_Y = 244
BALANCE_X = 24
BALANCE_Y = 268
RESET_7D_X = 200
RESET_7D_Y = 220
RESET_5H_X = 200
RESET_5H_Y = 244

# --- Bottom status area -----------------------------------------------------
# Shows the fault message when one is active, else the money readouts. Anchored
# by the text's ink box so the measured corner is exact. The money layout
# (positions/format for the three values) is still provisional — see render.py.
BOTTOM_TEXT_POS = (10, 296)   # top-left of the visible CAPITALS of the message
BOTTOM_TEXT_PT = 15           # point size (art is 72 DPI → 1 pt = 1 px)
