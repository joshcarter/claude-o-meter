import asyncio
import math
import time
from . import state


async def fake_loop(poll_seconds: int = 60) -> None:
    """Oscillate snapshot fields for offline development. No network, no Store."""
    t0 = time.time()
    while True:
        elapsed = time.time() - t0
        # Complete cycle every 5 minutes for a lively demo
        phase = (elapsed % 300) / 300  # 0..1

        five_pct = 40.0 + 40.0 * math.sin(2 * math.pi * phase)
        seven_pct = 30.0 + 30.0 * math.sin(2 * math.pi * phase + 1.0)

        now = int(time.time())
        five_hours_remaining = 4.0
        seven_days_remaining = 5.0 * 24.0

        five_sustainable = max((100.0 - five_pct) / five_hours_remaining, 0.001)
        five_burn = five_pct * 0.2
        seven_sustainable = max((100.0 - seven_pct) / seven_days_remaining, 0.001)
        seven_burn = seven_pct * 0.01

        state.snapshot.five_hour_pct = five_pct
        state.snapshot.five_hour_resets_at = now + int(five_hours_remaining * 3600)
        state.snapshot.five_hour_burn_rate = five_burn
        state.snapshot.five_hour_sustainable_rate = five_sustainable
        state.snapshot.five_hour_redline_ratio = min(five_burn / five_sustainable, 10.0)
        state.snapshot.seven_day_pct = seven_pct
        state.snapshot.seven_day_resets_at = now + int(seven_days_remaining * 3600)
        state.snapshot.seven_day_burn_rate = seven_burn
        state.snapshot.seven_day_sustainable_rate = seven_sustainable
        state.snapshot.seven_day_redline_ratio = min(seven_burn / seven_sustainable, 10.0)

        # TD-12.5: oscillate money fields so the display can be developed offline
        extra_used = 5.0 + 5.0 * math.sin(2 * math.pi * phase + 2.0)   # $0–$10
        state.snapshot.extra_usage_used = round(extra_used, 2)
        state.snapshot.extra_usage_limit = 20.0
        state.snapshot.extra_usage_enabled = True
        state.snapshot.balance = round(100.0 + 20.0 * math.sin(2 * math.pi * phase + 0.5), 2)

        state.snapshot.stale = False
        state.snapshot.auth_failed = False
        state.snapshot.last_update = now

        await asyncio.sleep(poll_seconds)
