#!/usr/bin/env python3
"""Non-faked evidence check: every screenshot artifact's recorded sha256 +
byte_size must match the ACTUAL on-disk PNG bytes.

Usage:
    python tests/verify_artifact_sha.py <run_[a-f0-9]{12}>

Opens the run-dir trace.jsonl, and for every screenshot ArtifactRecord recomputes
the sha256 of the on-disk PNG (at the exact path the Plinth HetznerNativeDriver
resolves the storage_key to) and asserts it equals the recorded sha256 and that
byte_size matches. Exits non-zero on any mismatch, missing file, or non-PNG bytes.
This is the guard against synthesized/placeholder frames: a fabricated record
whose bytes were not actually captured would fail here.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

PROJECT_SLUG = "synthetic-emr-demo"
RUN_ID_RE = re.compile(r"^run_[a-f0-9]{12}$")
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def run_dir(run_id: str) -> Path:
    home = os.environ.get("HOME", "/home/clawd")
    return Path(home) / "clawd" / "state" / "projects" / PROJECT_SLUG / "runs" / run_id


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not RUN_ID_RE.match(argv[1]):
        print("usage: verify_artifact_sha.py <run_[a-f0-9]{12}>", file=sys.stderr)
        return 2
    run_id = argv[1]
    rd = run_dir(run_id)
    trace = rd / "trace.jsonl"
    if not trace.is_file():
        print(f"ERROR: trace.jsonl not found for {run_id} at {trace}", file=sys.stderr)
        return 2

    screenshots = []
    for line in trace.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        if rec.get("kind") == "artifact" and rec.get("artifact_type") == "screenshot":
            screenshots.append(rec)

    if not screenshots:
        print("ERROR: no screenshot artifacts recorded in trace", file=sys.stderr)
        return 1

    failures = 0
    for a in screenshots:
        # Disk path the HetznerNativeDriver reads: runs/<runId>/<step_id>/<leaf>
        leaf = a["storage_key"].split("/")[-1]
        disk = rd / a["step_id"] / leaf
        if not disk.is_file():
            print(f"MISSING: {disk}", file=sys.stderr)
            failures += 1
            continue
        body = disk.read_bytes()
        if body[:8] != PNG_MAGIC:
            print(f"NOT-A-PNG: {disk}", file=sys.stderr)
            failures += 1
        actual_sha = hashlib.sha256(body).hexdigest()
        if actual_sha != a["sha256"]:
            print(
                f"SHA-MISMATCH: {disk}\n  recorded={a['sha256']}\n  actual  ={actual_sha}",
                file=sys.stderr,
            )
            failures += 1
        if len(body) != a["byte_size"]:
            print(
                f"SIZE-MISMATCH: {disk} recorded={a['byte_size']} actual={len(body)}",
                file=sys.stderr,
            )
            failures += 1
        if failures == 0 or actual_sha == a["sha256"]:
            print(f"OK {a['step_id']}/{leaf} sha256={actual_sha[:16]}… bytes={len(body)}")

    if failures:
        print(f"FAILED: {failures} artifact check(s) failed", file=sys.stderr)
        return 1
    print(f"PASS: {len(screenshots)} screenshot artifact(s) verified against on-disk PNG bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
