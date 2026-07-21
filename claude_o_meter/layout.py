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
# The bars are revealed left→right by a tall dim rectangle that spans the full
# bar height (TACH_DIM_TOP..TACH_DIM_BOTTOM) and slides horizontally. Its left
# edge sits at TACH_DIM_LEFT0 when fully dimmed (0 lit) and advances right by
# TACH_PITCH per revealed segment; the right/top/bottom edges are fixed.
# Geometry: 20 bars × 15 px + 19 gaps × 8 px = 452 px content, margins 14/14
# on a 480-wide screen → dim bounds [14,75]–[466,287]. Pitch = 15+8 = 23.
# Driven by 5h redline_ratio via gauges.tach_position().
TACH_SEGMENTS = 20
TACH_DIM_LEFT0 = 14     # dim left edge with 0 segments lit
TACH_PITCH = 23         # px the left edge advances per lit segment (bar+gap)
TACH_DIM_TOP = 75
TACH_DIM_RIGHT = 466
TACH_DIM_BOTTOM = 287

# --- Two-digit 0–99 readout (numeric form of the tach) ----------------------
# DSEG7 Modern Mini Italic. Drawn as a dim "88" ghost (all segments) with the
# live value bright over it. NUM_POS is the top-left of the visible "88".
NUM_POS = (246, 186)

# --- 25-segment fuel gauges (three side-by-side horizontal bars) ------------
# Three gauges left→right — 5-hour, 7-day, Fable — each a horizontal run of
# 25 bars, 3 px wide with a 2 px gap (FUEL_BAR_PITCH = 5 px/bar). Content width
# is 25·3 + 24·2 = 123 px. Remaining = clamp(100 − utilization, 0, 100) maps
# linearly onto the 25 bars, revealed left→right; the dim rectangle is pinned
# at the band RIGHT and its left edge advances by FUEL_BAR_PITCH per lit bar
# (see render.dim_fuel) so empty dims the whole band and full dims nothing.
FUEL_SEGMENTS = 25
FUEL_BAR_W = 3
FUEL_GAP = 2
FUEL_BAR_PITCH = 5       # px per bar: 3 px lit bar + 2 px gap
# 5-hour: [15,28]–[138,40]
FUEL_5H_DIM_LEFT = 15
FUEL_5H_DIM_TOP = 28
FUEL_5H_DIM_RIGHT = 138
FUEL_5H_DIM_BOTTOM = 40
# 7-day:  [178,28]–[301,40]
FUEL_7D_DIM_LEFT = 178
FUEL_7D_DIM_TOP = 28
FUEL_7D_DIM_RIGHT = 301
FUEL_7D_DIM_BOTTOM = 40
# Fable:  [342,28]–[465,40]
FUEL_FABLE_DIM_LEFT = 342
FUEL_FABLE_DIM_TOP = 28
FUEL_FABLE_DIM_RIGHT = 465
FUEL_FABLE_DIM_BOTTOM = 40

# --- Warning lights (dimmed when OFF; lit = condition true) -----------------
# Rects are (x, y, w, h). Both lights sit under the tach dim region, so the tach
# dim punches them out and each light is dimmed solely by its own rect —
# otherwise the overlap would dim them twice (too dark) or hold them off.
CHECK_ENGINE_RECT = (13, 138, 48, 46)   # (13,138)–(61,184)
LOW_FUEL_RECT = (13, 82, 48, 46)       # (13,82)–(61,128)

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
MONEY_POINT_PT = 25
MONEY_LABEL_PT = 15

# (label, group top-left, Snapshot field). Drawn when there is no active fault.
MONEY_GROUPS = (
    ("Extra", (14, 290), "extra_usage_used"),
    ("Limit", (169, 290), "extra_usage_limit"),
    ("Balance", (324, 290), "balance"),
)

# --- Reset readouts + static labels (always drawn) --------------------------
# Absolute top-left (visible-ink) positions. Each fuel column has a title above
# the bars and a DSEG reset value below them. 7-Day and Fable are weekly windows
# shown as dates ("YYYY - MM - DD" over the "8888  88  88" ghost, with two dashes
# overlaying the group gaps); 5-Hour is a time ("HH:MM" over "88:88") with a
# "resets at" sub-label. Each DSEG field is drawn over a dim all-segments ghost.
# Labels are Roboto Condensed Bold Italic; fields are DSEG7 Modern Mini Bold
# Italic.
#
# 5-Hour column (under the 5h fuel gauge): title, "resets at", HH:MM value.
RESET_5H_LABEL_POS = (12, 10)     # "5 Hour"
RESET_5H_SUBLABEL_POS = (12, 52)  # "resets at"
RESET_5H_TIME_POS = (81, 47)      # time over "88:88"
# 7-Day column: title above bars, date below.
RESET_7D_LABEL_POS = (175, 10)    # "7 Day"
RESET_7D_DATE_POS = (174, 47)     # date over "8888  88  88"
RESET_7D_DASH_Y = 55              # dash ink-top; x is computed from the gaps
# Fable column: title above bars, date below.
RESET_FABLE_LABEL_POS = (339, 10)  # "Fable"
RESET_FABLE_DATE_POS = (338, 47)   # date over "8888  88  88"
RESET_FABLE_DASH_Y = 55            # dash ink-top; x is computed from the gaps
RESET_LABEL_PT = 15               # Roboto Condensed Bold Italic
RESET_FIELD_PT = 18               # DSEG date/time fields
# px trimmed from each DSEG *digit* advance in the date fields, tightening the
# digits within a group so the field clears the tach arc. Inter-group spaces
# (and thus the dash gaps) are left alone. See render._render_condensed.
RESET_DATE_TRACKING = 1
DASH_PT = 20
DATE_GHOST = "8888  88  88"
TIME_GHOST = "88:88"

# --- Bottom status area -----------------------------------------------------
# Shows the fault message when one is active, else the money readouts. Anchored
# by the text's ink box so the measured corner is exact. The money layout
# (positions/format for the three values) is still provisional — see render.py.
BOTTOM_TEXT_POS = (10, 296)   # top-left of the visible CAPITALS of the message
BOTTOM_TEXT_PT = 15           # point size (art is 72 DPI → 1 pt = 1 px)
