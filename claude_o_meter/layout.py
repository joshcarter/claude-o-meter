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

# Dimming-rectangle default opacity (0–255). 212 ≈ 83%, matches the PyPortal
# ghost. config.toml's DIM_OPACITY overrides this per-deployment at the call site.
DIM_DEFAULT_OPACITY = 212

# --- Colours (RGB) — from code.py C_* palette -------------------------------
C_BG = (0x00, 0x00, 0x00)      # background
C_DARK = (0x0B, 0x1D, 0x20)    # unlit "ghost" segments
C_LIGHT = (0x40, 0xA9, 0xBF)   # lit segments / live readouts
C_ERROR = (0xFF, 0x22, 0x00)   # fault text

# --- Horizontal 20-segment tach bar (right-pinned dim) ----------------------
# Reveals left→right; driven by 5h redline_ratio via gauges.tach_position().
TACH_SEGMENTS = 20
TACH_X = 24
TACH_Y = 40
TACH_W = 432
TACH_H = 48

# --- Two-digit 0–99 readout (numeric form of the tach) ----------------------
NUM_X = 200
NUM_Y = 120

# --- Vertical 20-segment fuel gauge (top-pinned dim, drains top→bottom) ------
# remaining = clamp(100 − seven_day.utilization, 0, 100), linear.
FUEL_SEGMENTS = 20
FUEL_X = 408
FUEL_Y = 120
FUEL_W = 48
FUEL_H = 176

# --- Warning lights ---------------------------------------------------------
LOW_FUEL_X = 24
LOW_FUEL_Y = 120
CHECK_ENGINE_X = 24
CHECK_ENGINE_Y = 160
LIGHT_W = 40
LIGHT_H = 40

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

# --- Fault message overlay --------------------------------------------------
MSG_X = SCREEN_W // 2
MSG_Y = SCREEN_H - 24
