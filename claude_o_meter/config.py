import tomllib
from dataclasses import dataclass

_DEFAULTS: dict = {
    "DATA_SOURCE": "fake",
    "POLL_SECONDS": 60,
    "UTC_OFFSET_HOURS": 0,
    "DISPLAY_MODE": "window",
    "DIM_OPACITY": 212,
}


@dataclass
class Config:
    data_source: str
    poll_seconds: int
    utc_offset_hours: int
    display_mode: str
    dim_opacity: int


def load_config(path: str = "claude_o_meter/config.toml") -> Config:
    try:
        with open(path, "rb") as f:
            raw = tomllib.load(f)
    except FileNotFoundError:
        raw = {}
    d = {**_DEFAULTS, **raw}
    return Config(
        data_source=str(d["DATA_SOURCE"]),
        poll_seconds=int(d["POLL_SECONDS"]),
        utc_offset_hours=int(d["UTC_OFFSET_HOURS"]),
        display_mode=str(d["DISPLAY_MODE"]),
        dim_opacity=int(d["DIM_OPACITY"]),
    )
