#!/usr/bin/env python3
"""Stage 1: turn the answer key into a leak-free question set.

Reads data/policy_platform/answer_key_v1.json and writes
runs/<run_id>/queries.jsonl containing ONLY the six permitted fields per row:

    {row_id, payer, plan_type, state, cpt, procedure_name}

No URL, no doc_key, no row_class, no attestation, no LCD identifier. The
retrieval stage reads queries.jsonl and never opens the key. This is the
structural isolation the T004 card demands, enforced by code rather than by
convention: the retrieval subprocess cannot see what this file does not write.

    python3 scripts/policy_eval/emit_queries.py --run-id demo --limit 2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from policy_eval.common import (  # noqa: E402
    RUNS_DIR,
    key_sha256,
    load_key,
    write_json,
    write_jsonl,
)
from policy_eval.denominators import denominators  # noqa: E402
from policy_eval.leakcheck import (  # noqa: E402
    assert_query_fields,
    key_url_inventory,
)


def build_queries(
    key: dict[str, Any], row_ids: list[str] | None = None, limit: int | None = None
) -> list[dict[str, Any]]:
    procedure = key.get("procedure") or "Total knee arthroplasty"
    rows = key["rows"]
    if row_ids:
        wanted = list(row_ids)
        by_id = {r["id"]: r for r in rows}
        missing = [r for r in wanted if r not in by_id]
        if missing:
            raise SystemExit(f"unknown row ids: {missing}")
        rows = [by_id[r] for r in wanted]
    if limit is not None:
        rows = rows[:limit]
    queries = [
        {
            "row_id": r["id"],
            "payer": r["payer"],
            "plan_type": r["plan_type"],
            "state": r["state"],
            "cpt": r["cpt"],
            "procedure_name": procedure,
        }
        for r in rows
    ]
    assert_query_fields(queries)
    return queries


def emit(
    run_id: str, row_ids: list[str] | None = None, limit: int | None = None
) -> Path:
    key = load_key()
    denominators(key)  # abort before anything else if the key drifted
    queries = build_queries(key, row_ids, limit)
    run_dir = RUNS_DIR / run_id
    out = run_dir / "queries.jsonl"
    write_jsonl(out, queries)

    inventory = key_url_inventory(key)
    write_json(
        run_dir / "key_inventory.json",
        {
            "purpose": (
                "Forbidden strings for the retrieval prompt leak check. Derived "
                "from the answer key so a key edit widens the check automatically."
            ),
            "key_sha256": key_sha256(),
            **inventory,
        },
    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--rows", nargs="*", default=None, help="explicit row ids")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    out = emit(args.run_id, args.rows, args.limit)
    n = sum(1 for _ in out.open())
    print(f"wrote {n} queries to {out}")
    print("fields per query: row_id, payer, plan_type, state, cpt, procedure_name")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
