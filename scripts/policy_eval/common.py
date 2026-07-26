#!/usr/bin/env python3
"""Shared primitives for the policy-retrieval eval harness (rubric v1.4).

Nothing in this module reads the answer key on behalf of the retrieval model.
The key loader here is used only by the query emitter, the graders and the
report writer, all of which run on the harness side of the isolation boundary.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit

REPO_ROOT = Path(__file__).resolve().parents[2]
KEY_PATH = REPO_ROOT / "data" / "policy_platform" / "answer_key_v1.json"
RUBRIC_PATH = (
    REPO_ROOT
    / "docs"
    / "goals"
    / "policy-retrieval-eval"
    / "notes"
    / "scoring-rubric-v1.md"
)
RUNS_DIR = REPO_ROOT / "runs"

def _read_rubric_version() -> str:
    # Hardcoding this drifted once: the rubric moved to 1.4 while three modules
    # still stamped 1.3 into run artifacts, mislabelling the very artifact that
    # exists to make a post-hoc rubric edit detectable.
    m = re.search(
        r"^`rubric_version:\s*([0-9]+\.[0-9]+)`",
        RUBRIC_PATH.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    if not m:
        raise RuntimeError(f"cannot parse rubric_version from {RUBRIC_PATH}")
    return m.group(1)


RUBRIC_VERSION = _read_rubric_version()

# Rubric section 2 Tier 1: strip query parameters EXCEPT semantically required
# ones. The rubric names LCDId, ncdid and policyId. articleId is included here
# under the same principle and is recorded as a deviation in the harness note:
# every CMS Billing and Coding Article URL differs ONLY by articleId, so
# stripping it would normalise A56796 and A59811 to the same string and would
# manufacture false CORRECT grades on exactly the rows this benchmark exists to
# test. `ver` is kept for the same reason (it selects a document version).
SEMANTIC_QUERY_PARAMS = {"lcdid", "ncdid", "policyid", "articleid", "ver"}

LOGIN_PATH_RE = re.compile(r"/(login|signin|sign-in|idp|auth)\b", re.IGNORECASE)
SIGNIN_FORM_RE = re.compile(
    r"(<form[^>]*(login|signin|sign-in)|name=[\"']password[\"']"
    r"|type=[\"']password[\"']|please\s+sign\s+in|log\s?in\s+to\s+continue)",
    re.IGNORECASE,
)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def load_key(path: Path | None = None) -> dict[str, Any]:
    return json.loads(Path(path or KEY_PATH).read_text())


def key_sha256(path: Path | None = None) -> str:
    return file_sha256(Path(path or KEY_PATH))


def rubric_sha256(path: Path | None = None) -> str:
    return file_sha256(Path(path or RUBRIC_PATH))


def exact_binomial_upper_bound(n: int, alpha: float = 0.05) -> float:
    """95% one-sided upper bound on a rate given ZERO observed events.

    Rubric section 0.1: 1 - 0.05 ** (1 / N). The 3/N rule-of-three shorthand is
    forbidden anywhere in this harness because it overstates every bound.
    """
    if n <= 0:
        raise ValueError("N must be positive")
    return 1.0 - alpha ** (1.0 / n)


def format_bound(n: int) -> str:
    return f"{exact_binomial_upper_bound(n) * 100:.1f}%"


def normalize_url(url: str | None) -> str | None:
    """Rubric section 2 Tier 1 normalisation.

    Lowercase host, strip `www.`, strip scheme difference, strip fragment,
    strip trailing slash, strip query parameters except semantically required
    ones.
    """
    if not url or not isinstance(url, str):
        return None
    u = url.strip()
    if not u:
        return None
    if "//" not in u:
        u = "//" + u
    parts = urlsplit(u if "://" in u else "http:" + u)
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = parts.path or ""
    while path.endswith("/") and len(path) > 1:
        path = path[:-1]
    if path == "/":
        path = ""
    kept = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() in SEMANTIC_QUERY_PARAMS
    ]
    kept.sort(key=lambda kv: kv[0].lower())
    kept = [(k.lower(), v) for k, v in kept]
    q = urlencode(kept)
    out = host + path
    if q:
        out += "?" + q
    return out


def url_host(url: str | None) -> str | None:
    if not url or not isinstance(url, str):
        return None
    u = url.strip()
    if "://" not in u:
        u = "http://" + u
    host = (urlsplit(u).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host or None


def strip_html(html: str) -> str:
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )
    return re.sub(r"\s+", " ", text).strip()


def pdf_text(data: bytes) -> str:
    try:
        import io

        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return re.sub(
            r"\s+", " ", " ".join((p.extract_text() or "") for p in reader.pages)
        )
    except Exception:
        return ""


def extract_text(data: bytes, content_type: str | None) -> str:
    ct = (content_type or "").lower()
    if "pdf" in ct or data[:5] == b"%PDF-":
        return pdf_text(data)
    try:
        raw = data.decode("utf-8", errors="replace")
    except Exception:
        return ""
    if "html" in ct or "<html" in raw[:4000].lower():
        return strip_html(raw)
    return re.sub(r"\s+", " ", raw).strip()


def contains_cpt_27447(text: str) -> bool:
    return bool(re.search(r"\b27447\b", text or ""))


def detect_login_wall(
    status: int | None, final_url: str | None, redirect_chain: list[str], body_text: str
) -> tuple[bool, str | None]:
    if status in (401, 403):
        return True, f"http_{status}"
    for u in list(redirect_chain) + ([final_url] if final_url else []):
        if u and LOGIN_PATH_RE.search(urlsplit(u).path or ""):
            return True, f"redirect_to_login:{u}"
    head = (body_text or "")[:20000]
    if SIGNIN_FORM_RE.search(head):
        return True, "signin_form_in_body"
    return False, None


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    out = []
    with Path(path).open() as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
