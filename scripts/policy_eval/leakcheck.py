#!/usr/bin/env python3
"""Answer-key leak inventory and prompt scanning.

The retrieval model may never see a key URL, a key host or a key document
identifier. This module builds the forbidden inventory from the key itself, so
a key edit automatically widens the check, and scans retrieval prompts for it.

The check runs on PROMPTS, which is the harness's own input to the model. It
deliberately does NOT run on tool observations: a URL the model finds by
searching the open web is the measurement, not a leak.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from policy_eval.common import url_host  # noqa: E402

# Hosts that carry no answer information because they are the whole public
# internet's Medicare index; still collected and still checked, because the
# rule is "no key host in a prompt" with no exceptions.
QUERY_FIELDS = ("row_id", "payer", "plan_type", "state", "cpt", "procedure_name")


def _walk(obj: Any):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, v
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield None, v
            yield from _walk(v)


def key_url_inventory(key: dict[str, Any]) -> dict[str, list[str]]:
    """Every URL, host and document identifier anywhere in the answer key."""
    urls: set[str] = set()
    doc_ids: set[str] = set()
    for k, v in _walk(key):
        if isinstance(v, str):
            for m in re.findall(r"https?://[^\s\"'<>)\]}]+", v):
                urls.add(m.rstrip(".,;"))
            if k in (
                "doc_key",
                "lcd_id",
                "billing_article_id",
                "policy_id",
            ) and re.fullmatch(r"[A-Za-z0-9._\-]{3,}", v):
                doc_ids.add(v)
    hosts = {h for h in (url_host(u) for u in urls) if h}
    return {
        "urls": sorted(urls),
        "hosts": sorted(hosts),
        "doc_ids": sorted(doc_ids),
    }


def scan_text(text: str, inventory: dict[str, list[str]]) -> list[dict[str, str]]:
    hits = []
    low = (text or "").lower()
    for u in inventory["urls"]:
        if u.lower() in low:
            hits.append({"kind": "url", "value": u})
    for h in inventory["hosts"]:
        if re.search(r"(?<![a-z0-9.-])" + re.escape(h.lower()), low):
            hits.append({"kind": "host", "value": h})
    for d in inventory["doc_ids"]:
        if re.search(r"(?<![A-Za-z0-9])" + re.escape(d.lower()) + r"(?![A-Za-z0-9])", low):
            hits.append({"kind": "doc_id", "value": d})
    return hits


def assert_no_leak(
    texts: dict[str, str], inventory: dict[str, list[str]]
) -> dict[str, Any]:
    """Raise on any leak. Returns the audit record that goes in the artifact."""
    all_hits: dict[str, list[dict[str, str]]] = {}
    for label, text in texts.items():
        hits = scan_text(text, inventory)
        if hits:
            all_hits[label] = hits
    record = {
        "checked_texts": sorted(texts),
        "inventory_sizes": {k: len(v) for k, v in inventory.items()},
        "leaks_found": all_hits,
        "passed": not all_hits,
    }
    if all_hits:
        raise AssertionError(
            "ANSWER KEY LEAK DETECTED in retrieval prompts: "
            + repr(all_hits)
            + "\nThe run is void. Do not grade it."
        )
    return record


def assert_query_fields(queries: list[dict[str, Any]]) -> None:
    """A query row may carry the six permitted fields and nothing else."""
    for q in queries:
        extra = set(q) - set(QUERY_FIELDS)
        if extra:
            raise AssertionError(
                f"query row {q.get('row_id')} carries forbidden fields: {sorted(extra)}"
            )
        missing = set(QUERY_FIELDS) - set(q)
        if missing:
            raise AssertionError(
                f"query row {q.get('row_id')} is missing fields: {sorted(missing)}"
            )
