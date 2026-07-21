#!/usr/bin/env python3
"""Capture raw claude.ai usage/credits responses to disk.

Mirrors the poller's request setup (curl_cffi with a Chrome TLS fingerprint,
since claude.ai gates on it) so what we capture is exactly what the live poller
sees. Use it to refresh the ``sample-*.json`` fixtures whenever Anthropic changes
the usage payload — e.g. adding a new per-model window like the Fable gauge.

Usage:
    CLAUDE_SESSION_KEY=... python tools/capture_usage.py [--out DIR]

Writes (pretty-printed) into --out (default: repo root):
    usage-capture.json            full /usage response
    prepaid-credits-capture.json  full /prepaid/credits response

The capture files are timestamped copies you can diff against the committed
``sample-usage.json`` / ``sample-prepaid-credits.json`` before promoting them.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from curl_cffi.requests import Session

CLAUDE_BASE = "https://claude.ai"


def _session_key() -> str:
    val = os.environ.get("CLAUDE_SESSION_KEY", "")
    if not val:
        sys.exit("CLAUDE_SESSION_KEY is not set — grab the `sessionKey` cookie from a logged-in claude.ai session")
    return val


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1],
                    help="directory to write capture files into (default: repo root)")
    args = ap.parse_args()

    key = _session_key()
    cookies = {"sessionKey": key}

    with Session(impersonate="chrome124") as session:
        org_id = os.environ.get("CLAUDE_ORG_ID")
        if not org_id:
            resp = session.get(f"{CLAUDE_BASE}/api/organizations", cookies=cookies, timeout=15)
            resp.raise_for_status()
            orgs = resp.json()
            if not orgs:
                sys.exit("No organizations returned")
            org_id = orgs[0]["uuid"]
        print(f"org_id: {org_id}")

        usage = session.get(f"{CLAUDE_BASE}/api/organizations/{org_id}/usage", cookies=cookies, timeout=15)
        usage.raise_for_status()
        usage_data = usage.json()

        credits = session.get(f"{CLAUDE_BASE}/api/organizations/{org_id}/prepaid/credits", cookies=cookies, timeout=15)
        credits_data = credits.json() if credits.status_code == 200 else {"_status": credits.status_code}

    usage_path = args.out / "usage-capture.json"
    credits_path = args.out / "prepaid-credits-capture.json"
    usage_path.write_text(json.dumps(usage_data, indent=2) + "\n")
    credits_path.write_text(json.dumps(credits_data, indent=2) + "\n")

    print(f"wrote {usage_path}")
    print(f"wrote {credits_path}")
    print("\nusage keys:", ", ".join(usage_data.keys()) if isinstance(usage_data, dict) else "(not an object)")


if __name__ == "__main__":
    main()
