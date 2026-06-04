# TODO

**Last updated:** 2026-06-04

Index for the **claude-o-meter** build: a single-process pygame dashboard,
developed desktop-first and later deployed to a Raspberry Pi 3. Work tracked
across split files; read in priority order.

<!-- next-td: TD-15 -->

## Project

Build **claude-o-meter**, one Python program that does *both* the polling and
the display — no second service, no HTTP seam between them. It reuses the
existing `server/src/` polling logic (curl_cffi, `polling_loop`) on a background
thread that writes the in-memory `state.snapshot`; the **pygame** main loop reads
that snapshot directly and renders the instrument cluster.

Bring-up order is **desktop-first**: develop the whole app on this Mac in a
**480×320 pygame window** (no Pi, no cookie required — a config-selected fake
data source drives the gauges), then deploy the same program to the Pi 3 driving
the PiTFT panel. **Desktop operation stays a supported, first-class target going
forward**, not just a dev convenience.

## Display design (the instrument cluster)

A 480×320 "dashboard" (a desktop window now, the PiTFT panel later — same
dimensions) where a single full-on bitmap per instrument is selectively
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

- **One process, not two.** Polling and display live in the same program
  (`claude-o-meter`). The poll loop runs on a background thread and publishes the
  in-memory `state.snapshot`; the pygame loop reads it directly. No FastAPI, no
  `/status` HTTP call, no `mock_server`.
- **Desktop-first and desktop-supported.** Primary dev + a permanent run target
  is a 480×320 pygame window on a desktop (macOS now). The Pi 3 + PiTFT is a
  second deployment of the same code, not a different program. Offline dev uses a
  config-selected fake data source — no live cookie or network needed.
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
| `TODO_CRITICAL.md` | Core path to a working dashboard (desktop first, then Pi 3). Work here first. |
| `TODO_BACKLOG.md`  | Enhancements once the core path runs end-to-end. |
| `TODO_DEFERRED.md` | Alternatives not chosen / blocked on input. Not read during automated refine. |
| `DONE.md`          | Completed TD trees, dated. |

## Triage table (where new TDs go)

- Blocks a working end-to-end dashboard (desktop window first, then Pi 3) → `TODO_CRITICAL.md`
- Improves a working dashboard → `TODO_BACKLOG.md`
- Rejected approach, or blocked on external input/hardware → `TODO_DEFERRED.md`
