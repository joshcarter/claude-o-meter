import os
import tomllib
from dataclasses import dataclass

_DEFAULTS: dict = {
    "DATA_SOURCE": "fake",
    "POLL_SECONDS": 180,
    "UTC_OFFSET_HOURS": 0,
    "DISPLAY_MODE": "window",
    "DIM_OPACITY": 212,
    "FB_DEVICE": "/dev/fb1",
}


@dataclass
class Config:
    data_source: str
    poll_seconds: int
    utc_offset_hours: int
    display_mode: str
    dim_opacity: int
    fb_device: str


def load_config(path: str = "claude_o_meter/config.toml") -> Config:
    try:
        with open(path, "rb") as f:
            raw = tomllib.load(f)
    except FileNotFoundError:
        raw = {}
    d = {**_DEFAULTS, **raw}
    # Environment variables override the TOML so a single committed config.toml
    # can serve both the Mac (window/fake) and the Pi service (framebuffer/live)
    # — the systemd unit sets DISPLAY_MODE/DATA_SOURCE without a per-host edit.
    for key in _DEFAULTS:
        if key in os.environ:
            d[key] = os.environ[key]
    return Config(
        data_source=str(d["DATA_SOURCE"]),
        poll_seconds=int(d["POLL_SECONDS"]),
        utc_offset_hours=int(d["UTC_OFFSET_HOURS"]),
        display_mode=str(d["DISPLAY_MODE"]),
        dim_opacity=int(d["DIM_OPACITY"]),
        fb_device=str(d["FB_DEVICE"]),
    )
