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

# --- Money readouts ---------------------------------------------------------
# Each readout is a group of four text elements at fixed offsets from the
# group's top-left corner (Affinity coordinates, 72 DPI → pt = px):
#
#   "$"        Roboto Condensed Bold Italic 15 pt at (0, 3)
#   value      DSEG7 Modern Mini Bold Italic 20 pt at (8, 0); drawn over a dim
#              "888 88" ghost in the field "DDD CC" (space = decimal point)
#   "."        Roboto Condensed Bold Italic 32 pt at (54, 15)
#   label      Roboto Condensed Bold Italic 15 pt at (95, 5)
#
# The three dollar digits sit in digit cells (so leading blanks register on the
# ghost), then a single natural space (4 px) before the two cent digits — the
# "." at +(54,15) overlays that gap.
MONEY_DOLLAR_OFF = (0, 3)
MONEY_VALUE_OFF = (8, 0)
MONEY_POINT_OFF = (54, 15)
MONEY_LABEL_OFF = (95, 5)
MONEY_DOLLAR_PT = 15
MONEY_VALUE_PT = 20
MONEY_POINT_PT = 32
MONEY_LABEL_PT = 15

# (label, group top-left, Snapshot field). Drawn when there is no active fault.
MONEY_GROUPS = (
    ("Extra", (10, 289), "extra_usage_used"),
    ("Limit", (170, 289), "extra_usage_limit"),
    ("Balance", (328, 289), "balance"),
)

# --- Reset readouts + static labels (always drawn, top area) ----------------
# Absolute top-left (visible-ink) positions. The two DSEG fields are drawn over
# a dim all-segments ghost (like the money value), but the date/time always have
# every digit, so the live string shares the ghost's structure and registers on
# it without per-cell packing. Labels/dashes are Roboto; fields are DSEG7 Modern
# Mini Bold Italic 20pt. The "7 Day" by the fuel gauge labels that instrument.
RESET_7D_LABEL_POS = (11, 12)     # "7 Day Reset"
RESET_7D_DATE_POS = (11, 30)      # "YYYY  MM  DD" over "8888  88  88"
RESET_5H_LABEL_POS = (11, 71)     # "5 Hour Reset"
RESET_5H_TIME_POS = (11, 88)      # "HH:MM" over "88:88"
DASH_1_POS = (77, 39)
DASH_2_POS = (77, 118)
FUEL_LABEL_POS = (422, 36)        # "7 Day" — labels the fuel gauge
RESET_LABEL_PT = 15
RESET_FIELD_PT = 20
DASH_PT = 15
DATE_GHOST = "8888  88  88"
TIME_GHOST = "88:88"

# --- Bottom status area -----------------------------------------------------
# Shows the fault message when one is active, else the money readouts. Anchored
# by the text's ink box so the measured corner is exact. The money layout
# (positions/format for the three values) is still provisional — see render.py.
BOTTOM_TEXT_POS = (10, 296)   # top-left of the visible CAPITALS of the message
BOTTOM_TEXT_PT = 15           # point size (art is 72 DPI → 1 pt = 1 px)
