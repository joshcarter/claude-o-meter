# TODO

**Last updated:** 2026-06-01

Index for the PyPortal → Raspberry Pi 3 conversion + display redesign. Work
tracked across split files; read in priority order.

<!-- next-td: TD-14 -->

## Project

Port the Claude usage dashboard off the Adafruit PyPortal (CircuitPython) onto
an **all-in-one Raspberry Pi 3** running two systemd services:

- `claude-poller` — the existing `server/` code, extended to capture extra-usage
  and prepaid-balance feeds (FastAPI + curl_cffi).
- `claude-display` — a new **pygame** client replacing `pyportal/code.py`.

The HTTP API (`/status`) is the fixed seam between them.

## Display design (the instrument cluster)

A 480×320 "dashboard" where a single full-on bitmap per instrument is selectively
darkened by **dimming rectangles** (black `SRCALPHA`, ~83% ≈ current ghost),
with the dim edge **snapped to segment boundaries**. Widgets:

| Widget | Source data | Mapping |
|--------|-------------|---------|
| Horizontal 20-seg **tach** bar (right-pinned dim, reveals left→right) | 5h `redline_ratio` | **burn rate** vs sustainable; redline = tokens exhaust exactly at window reset. Non-linear (`tach_position`). Unchanged from today. |
| Two-digit **0–99** readout | same as tach | numeric form of the tach |
| Vertical 20-seg **fuel gauge** (top-pinned dim, drains top→bottom) | 7d `utilization` | **remaining** = clamp(100 − util, 0, 100). Linear. |
| **Low-fuel** light | 7d `utilization` | on when remaining ≤ 20% (util ≥ 80%) |
| **Check-engine** light + message | fault state | poller-unreachable / data-stale / needs-auth |
| **Extra use $**, **Extra limit $**, **Balance $** | `extra_usage` + `/prepaid/credits` | cents → USD; up to 999.99 |
| **7-day reset date** | 7d `resets_at` | date (time maybe later) |
| **5-hour reset time** | 5h `resets_at` | time-of-day (`fmt_hhmm`) |

### Locked decisions

- Tach = burn-rate/`redline_ratio` (NOT raw utilization); current non-linear
  scaling kept. Fuel = linear 7d remaining. Two windows, two instrument types.
- All money fields are **cents** → divide by 100. `monthly_limit` (2000=$20) and
  balance `amount` (12000=$120) confirmed cents; `used_credits` assumed cents,
  **verify on first nonzero**.
- **USD only** this version; non-USD currency → treat value as unavailable
  (TD-13 deferred).
- Segments quantized; dim edge snaps to segment boundaries.
- Billing feeds (extra-usage, balance) poll slowly, are snapshot-only (no
  history), and their failures must NOT trip stale/check-engine.

## Pending user input (does not block structural work)

Exact pixel locations, segment-boundary coordinates, and font sizes/positions
are still to come. Build the renderer against named constants in a `layout`
module and fill values when provided.

## Files

| File | Holds |
|------|-------|
| `TODO_CRITICAL.md` | Core path to a working Pi 3 dashboard. Work here first. |
| `TODO_BACKLOG.md`  | Enhancements once the core path runs end-to-end. |
| `TODO_DEFERRED.md` | Alternatives not chosen / blocked on input. Not read during automated refine. |
| `DONE.md`          | Completed TD trees, dated. |

## Triage table (where new TDs go)

- Blocks a working end-to-end dashboard on the Pi 3 → `TODO_CRITICAL.md`
- Improves a working dashboard → `TODO_BACKLOG.md`
- Rejected approach, or blocked on external input/hardware → `TODO_DEFERRED.md`
