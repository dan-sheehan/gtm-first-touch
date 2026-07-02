#!/usr/bin/env python3
"""Seed or reseed the Harbor Analytics demo path."""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


DEMO_APPS = [
    ("ICP Scorer", "http://localhost:3012/api/seed"),
    ("Enrichment", "http://localhost:3011/api/seed"),
    ("Outbound Email", "http://localhost:3008/api/seed"),
    ("Discovery Prep", "http://localhost:3005/api/seed"),
]


def post_seed(url: str, *, force: bool) -> tuple[bool, dict[str, object] | str]:
    body = json.dumps({"force": force}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        return False, str(exc)

    try:
        return True, json.loads(payload)
    except json.JSONDecodeError:
        return False, payload


def format_result(label: str, ok: bool, result: dict[str, object] | str) -> str:
    if not ok:
        return f"  {label}: not running ({result})"

    status = str(result.get("status", "error"))
    count = int(result.get("count", 0))
    cleared = int(result.get("cleared", 0))
    existing = int(result.get("existing", 0))

    if status == "seeded":
        suffix = f"seeded {count}"
        if cleared:
            suffix += f" after clearing {cleared}"
        return f"  {label}: {suffix}"

    if status == "skipped":
        suffix = "skipped"
        if existing:
            suffix += f" ({existing} existing)"
        return f"  {label}: {suffix}"

    message = result.get("message") or result.get("error") or result
    return f"  {label}: {status} ({message})"


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed Harbor Analytics demo data.")
    parser.add_argument("mode", choices=["seed", "reseed"], help="seed skips existing data; reseed clears and reloads")
    args = parser.parse_args()

    force = args.mode == "reseed"
    print("Reseeding Harbor Analytics demo data..." if force else "Seeding Harbor Analytics demo data...")

    had_error = False
    for label, url in DEMO_APPS:
        ok, result = post_seed(url, force=force)
        if not ok:
            had_error = True
        print(format_result(label, ok, result))

    if had_error:
        print("Start the hub first with `make start`, then rerun this command.")
        return 1

    print("Done. Visit http://localhost:8000")
    return 0


if __name__ == "__main__":
    sys.exit(main())
