from dataclasses import dataclass
from typing import Optional


@dataclass
class Snapshot:
    five_hour_pct: Optional[float] = None
    five_hour_resets_at: Optional[int] = None
    five_hour_burn_rate: float = 0.0
    five_hour_sustainable_rate: Optional[float] = None
    five_hour_redline_ratio: Optional[float] = None
    seven_day_pct: Optional[float] = None
    seven_day_resets_at: Optional[int] = None
    seven_day_burn_rate: float = 0.0
    seven_day_sustainable_rate: Optional[float] = None
    seven_day_redline_ratio: Optional[float] = None
    seven_day_opus_pct: Optional[float] = None
    seven_day_opus_resets_at: Optional[int] = None
    extra_usage_used: Optional[float] = None    # USD
    extra_usage_limit: Optional[float] = None   # USD
    extra_usage_enabled: Optional[bool] = None
    balance: Optional[float] = None             # USD prepaid credit balance
    stale: bool = True
    auth_failed: bool = False
    last_update: int = 0


snapshot = Snapshot()
org_id: Optional[str] = None
