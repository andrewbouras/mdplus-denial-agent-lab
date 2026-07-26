#!/usr/bin/env python3
"""The only two capabilities the retrieval model is given: search and fetch.

SECRET HANDLING. The Brave Search subscription token is read from the
environment variable WEB_SEARCH_API_KEY at call time. It is never logged, never
written to a run artifact, never written to an MCP config file and never
returned to the model. Artifacts record only `search_backend: "Brave Search API"`
and the result count.
"""

from __future__ import annotations

import os
import socket
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from policy_eval.common import (  # noqa: E402
    contains_cpt_27447,
    detect_login_wall,
    extract_text,
    sha256_bytes,
)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
FETCH_TIMEOUT = 30
SEARCH_BACKEND = "Brave Search API"
SEARCH_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"


class SearchUnavailable(RuntimeError):
    pass


def search(query: str, count: int = 5) -> dict[str, Any]:
    """Web search via the Brave Search API. Returns title/url/snippet triples."""
    token = os.environ.get("WEB_SEARCH_API_KEY")
    if not token:
        raise SearchUnavailable(
            "WEB_SEARCH_API_KEY is not set. Refusing to run: a harness with no "
            "search path measures the network, not the model."
        )
    resp = requests.get(
        SEARCH_ENDPOINT,
        params={"q": query, "count": max(1, min(int(count), 20))},
        headers={"X-Subscription-Token": token, "Accept": "application/json"},
        timeout=FETCH_TIMEOUT,
    )
    if resp.status_code != 200:
        return {
            "backend": SEARCH_BACKEND,
            "query": query,
            "http_status": resp.status_code,
            "result_count": 0,
            "results": [],
            "error": f"search backend returned HTTP {resp.status_code}",
        }
    data = resp.json()
    results = []
    for r in (data.get("web") or {}).get("results", []):
        results.append(
            {
                "title": r.get("title"),
                "url": r.get("url"),
                "snippet": r.get("description"),
            }
        )
    return {
        "backend": SEARCH_BACKEND,
        "query": query,
        "http_status": 200,
        "result_count": len(results),
        "results": results,
        "error": None,
    }


BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"}


def _blocked_reason(url: str) -> str | None:
    """Second line of defence on the isolation boundary.

    `http_fetch` is one of only two capabilities the retrieval model has, so it
    must not become a file reader or a way onto this host's loopback interface.
    """
    parts = urlsplit(url)
    if parts.scheme.lower() not in ("http", "https"):
        return f"only http and https URLs are allowed, got scheme {parts.scheme!r}"
    host = (parts.hostname or "").lower()
    if not host:
        return "URL has no host"
    if host in BLOCKED_HOSTS or host.endswith(".local"):
        return "loopback and link-local hosts are not fetchable"
    if host.startswith(("10.", "192.168.", "169.254.")) or any(
        host.startswith(f"172.{n}.") for n in range(16, 32)
    ):
        return "private-network hosts are not fetchable"
    return None


def fetch(url: str, max_text_chars: int = 20000) -> dict[str, Any]:
    """Perform a REAL HTTP GET and record the observed facts.

    Adapted from scripts/run_policy_retrieval.py fetch() at L112-135 (the one
    reuse the T004 card permits for HTTP evidence capture), extended with the
    redirect chain, final URL, extracted text, login-wall detection, CPT-27447
    presence and host-resolution evidence that rubric section 6 Stage A needs.
    """
    blocked = _blocked_reason(url)
    if blocked:
        return {
            "url": url,
            "final_url": None,
            "status": None,
            "redirect_chain": [],
            "content_type": None,
            "bytes": 0,
            "sha256": None,
            "text": "",
            "text_truncated": False,
            "contains_cpt_27447": False,
            "login_wall": False,
            "login_wall_reason": None,
            "host": (urlsplit(url).hostname or "").lower() or None,
            "host_resolves": None,
            "error": f"blocked by harness: {blocked}",
        }
    host = (urlsplit(url).hostname or "").lower()
    host_resolves = None
    if host:
        try:
            socket.getaddrinfo(host, None)
            host_resolves = True
        except socket.gaierror:
            host_resolves = False

    if host_resolves is False:
        return {
            "url": url,
            "final_url": None,
            "status": None,
            "redirect_chain": [],
            "content_type": None,
            "bytes": 0,
            "sha256": None,
            "text": "",
            "text_truncated": False,
            "contains_cpt_27447": False,
            "login_wall": False,
            "login_wall_reason": None,
            "host": host,
            "host_resolves": False,
            "error": f"DNS resolution failed for host {host!r}",
        }

    try:
        resp = requests.get(
            url,
            timeout=FETCH_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            allow_redirects=True,
        )
        body = resp.content
        text = extract_text(body, resp.headers.get("content-type"))
        chain = [h.headers.get("location") or h.url for h in resp.history]
        login, login_reason = detect_login_wall(
            resp.status_code, resp.url, chain, text
        )
        return {
            "url": url,
            "final_url": resp.url,
            "status": resp.status_code,
            "redirect_chain": chain,
            "content_type": resp.headers.get("content-type"),
            "bytes": len(body),
            "sha256": sha256_bytes(body),
            "text": text[:max_text_chars],
            "text_truncated": len(text) > max_text_chars,
            "contains_cpt_27447": contains_cpt_27447(text),
            "login_wall": login,
            "login_wall_reason": login_reason,
            "host": host,
            "host_resolves": True,
            "error": None,
        }
    except requests.RequestException as exc:
        return {
            "url": url,
            "final_url": None,
            "status": None,
            "redirect_chain": [],
            "content_type": None,
            "bytes": 0,
            "sha256": None,
            "text": "",
            "text_truncated": False,
            "contains_cpt_27447": False,
            "login_wall": False,
            "login_wall_reason": None,
            "host": host,
            "host_resolves": host_resolves,
            "error": str(exc),
        }
