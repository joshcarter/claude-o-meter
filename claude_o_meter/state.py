from dataclasses import dataclass
from typing import Optional


@dataclass
class Snapshot:
    five_hour_pct: Optional[float] = None
    five_hour_resets_at: Optional[int] = None
    five_hour_burn_rate: Optional[float] = None  # None = not enough history yet
    five_hour_sustainable_rate: Optional[float] = None
    five_hour_redline_ratio: Optional[float] = None
    # True after a successful poll that still has no 5h burn estimate (neither
    # regression nor window-average provisional); drives the "collecting data"
    # warm-up message instead of a 0 tach.
    five_hour_warming_up: bool = False
    seven_day_pct: Optional[float] = None
    seven_day_resets_at: Optional[int] = None
    seven_day_burn_rate: Optional[float] = None  # None = not enough history yet
    seven_day_sustainable_rate: Optional[float] = None
    seven_day_redline_ratio: Optional[float] = None
    seven_day_opus_pct: Optional[float] = None
    seven_day_opus_resets_at: Optional[int] = None
    # Fable: a weekly, model-scoped window sourced from the usage response's
    # limits[] array (scope.model.display_name == "Fable"). Mirrors the 7-day
    # fields — same weekly burn/redline treatment.
    fable_pct: Optional[float] = None
    fable_resets_at: Optional[int] = None
    fable_burn_rate: Optional[float] = None  # None = not enough history yet
    fable_sustainable_rate: Optional[float] = None
    fable_redline_ratio: Optional[float] = None
    extra_usage_used: Optional[float] = None    # USD
    extra_usage_limit: Optional[float] = None   # USD
    extra_usage_enabled: Optional[bool] = None
    balance: Optional[float] = None             # USD prepaid credit balance
    error: Optional[str] = None                 # human-readable fault cause, or None when healthy
    last_update: int = 0


snapshot = Snapshot()
org_id: Optional[str] = None
