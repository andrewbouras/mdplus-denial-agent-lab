#!/usr/bin/env python3
"""Guards for the fetch path, added by T018 on the Judge T017 ruling and
extended by T020.

Four defects motivate this file, and all four pushed the benchmark in the
flattering direction, which is why they are fixed before the first eval run
rather than after it.

1. One payer host answers a non-browser request with HTTP 200 and a stub of
   about 930 bytes. `detect_login_wall` returned (False, None) on that stub, so
   the harness could not tell a blocked fetch from a successful one. A blocked
   fetch makes the retrieval model abstain, and abstention is the behaviour the
   headline metric rewards, so undetected blocking would have scored our own
   network conditions as model caution.
2. `strip_html` unescaped entities AFTER stripping tags, so escaped markup
   inside a JSON payload survived as a literal tag in the text the retrieval
   model reads.
3. A raw substring identity test manufactures phantoms on live payer HTML.
4. `strip_html` stripped `<[^>]*>`, which is not tag shaped. A bare "<" in
   ordinary prose, for example "joint space < 2 mm" in a payer PDF, deleted
   every character up to the next ">". On the Carelon joint surgery guideline
   that silently removed the passage carrying CPT 27447. Found by T020.

These tests are offline and deterministic. They make no network request. Run
them with pytest, or directly with `python3 tests/test_policy_eval_fetch_guards.py`,
because pytest is not installed in this environment today.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from policy_eval.common import (  # noqa: E402
    detect_bot_block,
    detect_login_wall,
    normalize_for_match,
    normalized_contains,
    strip_html,
)

# The verbatim stub the Horizon host returned to a bare curl on 2026-07-26.
IMPERVA_STUB_TEXT = (
    "Request unsuccessful. Incapsula incident ID: "
    "914000070904437332-329831614124261862"
)
IMPERVA_STUB_HTML = (
    "<html><head><META NAME=\"ROBOTS\" CONTENT=\"NOINDEX, NOFOLLOW\">"
    "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\">"
    "<script src=\"/_Incapsula_Resource?SWJIYLWA=719d34d31c8e3a6e6fffd425f7e032f3\">"
    "</script></head><body>Request unsuccessful. Incapsula incident ID: "
    "914000070904437332-329831614124261862</body></html>"
)


# --------------------------------------------------------------------------
# 1. Bot-block detection
# --------------------------------------------------------------------------


def test_imperva_stub_is_detected_as_a_bot_block() -> None:
    blocked, reason = detect_bot_block(200, {}, IMPERVA_STUB_TEXT, 931)
    assert blocked is True
    assert reason


def test_imperva_stub_markers_survive_in_raw_html() -> None:
    blocked, reason = detect_bot_block(
        200, {"Content-Type": "text/html"}, IMPERVA_STUB_HTML, 931
    )
    assert blocked is True
    assert reason == "imperva_incapsula_resource"


def test_bot_block_and_login_wall_stay_separate() -> None:
    """A bot block is OUR artefact. A login wall is the PAYER's property.

    The stub must never be read as a login wall, because a login wall puts a row
    in the gated class and gated rows earn full credit for abstention.
    """
    assert detect_login_wall(200, "https://example.org/x", [], IMPERVA_STUB_TEXT) == (
        False,
        None,
    )
    assert detect_bot_block(200, {}, IMPERVA_STUB_TEXT, 931)[0] is True


def test_named_vendor_fingerprints() -> None:
    cases = {
        "Attention Required! | Cloudflare": "cloudflare_attention_required",
        "<script>window.__cf_chl_opt={};</script>": "cloudflare_challenge",
        "<title>Just a moment...</title>": "cloudflare_just_a_moment",
        "<div id='px-captcha'></div>": "perimeterx_captcha",
        "<script src='https://js.datadome.co/tags.js'></script>": "datadome",
        "Reference #97.1a2b.errors.edgesuite.net": "akamai_edgesuite_error",
        "cf-browser-verification cookie": "cloudflare_browser_verification",
    }
    for body, expected in cases.items():
        blocked, reason = detect_bot_block(200, {}, body, len(body))
        assert blocked is True, body
        assert reason == expected, (body, reason)


def test_generic_thin_200_rule() -> None:
    blocked, reason = detect_bot_block(200, {}, "<html><body>Access denied</body></html>", 900)
    assert blocked is True
    assert reason.startswith("thin_200_response")


def test_thin_body_carrying_cpt_27447_is_not_a_block() -> None:
    body = "<html><body>Prior authorization required for CPT 27447.</body></html>"
    assert detect_bot_block(200, {}, body, len(body)) == (False, None)


def test_real_policy_page_is_not_a_block() -> None:
    body = "<html><body>" + ("Knee arthroplasty policy text. " * 100) + "</body></html>"
    assert detect_bot_block(200, {}, body, len(body)) == (False, None)


def test_non_200_is_never_a_generic_block() -> None:
    """A 403 is a real refusal and belongs to the login-wall path, not here."""
    assert detect_bot_block(403, {}, "Forbidden", 9) == (False, None)
    assert detect_bot_block(404, {}, "Not found", 9) == (False, None)


def test_short_pdf_extraction_is_not_called_a_block() -> None:
    """A PDF whose text will not extract is a parser failure, not a block.

    Calling it a block would move the row out of the scored denominator, and
    that is the flattering direction.
    """
    assert detect_bot_block(200, {"Content-Type": "application/pdf"}, "", 400000) == (
        False,
        None,
    )


# --------------------------------------------------------------------------
# 2. strip_html ordering
# --------------------------------------------------------------------------


def test_escaped_markup_does_not_leak_a_literal_tag() -> None:
    """The exact case proved live on 2026-07-26 before the fix."""
    out = strip_html("(&lt;abbr&gt;NCD&lt;/abbr&gt;)")
    assert "<abbr>" not in out
    assert "abbr" not in out
    assert "NCD" in out


def test_doubly_escaped_markup_resolves() -> None:
    assert "<abbr>" not in strip_html("(&amp;lt;abbr&amp;gt;NCD&amp;lt;/abbr&amp;gt;)")


def test_ordinary_entities_still_unescape() -> None:
    assert "Medicare & Medicaid" in strip_html("Medicare &amp; Medicaid")
    assert strip_html("<p>a&nbsp;b</p>") == "a b"


def test_script_and_style_content_is_removed() -> None:
    html = "<style>.a{color:red}</style><script>var x=1;</script><p>Policy</p>"
    assert strip_html(html) == "Policy"


def test_a_bare_angle_bracket_does_not_eat_the_document() -> None:
    """The sixth false absence on this board, found live during T020.

    The tag pattern used to be `<[^>]*>`, which is not tag shaped: it matches a
    bare `<` followed by anything up to the next `>`. Payer PDFs are full of
    ordinary prose like "less than 5 mm" rendered as "< 5 mm", and PDF text
    extraction emits those characters literally. One stray `<` therefore
    deleted every character up to the next `>`, which on the Carelon joint
    surgery guideline swallowed the passage containing CPT 27447.

    The failure was SILENT. No error, no exception, a plausible looking body of
    text, and an attestation quote reported as absent from a document that
    plainly contains it. An absent quote pushes a row toward abstention, and
    abstention earns full credit under the headline metric, so this defect
    flatters us. That is why it is pinned by a test.
    """
    text = strip_html("Perform if the defect is < 5 mm and CPT 27447 applies.")
    assert "27447" in text
    assert "5 mm" in text
    # A real tag on the same line must still be removed.
    assert strip_html("<p>gap < 5 mm</p>") == "gap < 5 mm"


def test_a_bare_less_than_inside_pdf_text_keeps_the_cpt_code() -> None:
    """The same defect at the level the harness actually consumes it."""
    from policy_eval.common import contains_cpt_27447

    body = "Criteria: joint space < 2 mm. Codes covered: 27447, 27446."
    assert contains_cpt_27447(strip_html(body)) is True


# --------------------------------------------------------------------------
# 3. Normalised matching
# --------------------------------------------------------------------------


def test_normalised_match_survives_markup_inside_the_quote() -> None:
    """The bm_0057 case. A raw substring test reported a phantom absence."""
    page = (
        "<p>criteria outlined in National Coverage Determinations "
        "(&lt;abbr&gt;NCD&lt;/abbr&gt;), Local Coverage Determination "
        "(&lt;abbr&gt;LCD&lt;/abbr&gt;)</p>"
    )
    quote = (
        "criteria outlined in National Coverage Determinations (NCD), "
        "Local Coverage Determination (LCD)"
    )
    assert quote not in page
    assert normalized_contains(page, quote) is True


def test_normalised_match_survives_ampersand_escaping() -> None:
    """The bm_0061 case. Its own quote is absent from the raw bytes."""
    page = "<div>we follow Centers for Medicare &amp; Medicaid Services (CMS) guidelines</div>"
    quote = "we follow Centers for Medicare & Medicaid Services (CMS) guidelines"
    assert normalized_contains(page, quote) is True


def test_normalised_match_survives_curly_quotes_and_whitespace() -> None:
    page = "<p>Medicare requires use of\n   the Manual and NCD/LCD’s first.</p>"
    quote = "Medicare requires use of the Manual and NCD/LCD's first."
    assert normalized_contains(page, quote) is True


def test_normalised_match_still_fails_on_different_text() -> None:
    """The matcher must not be so loose that it can no longer find a real change."""
    page = "<p>Blue Cross NC staff will perform clinical reviews.</p>"
    assert normalized_contains(page, "Blue Cross NC staff will not review") is False
    assert normalized_contains(page, "an entirely different sentence") is False


def test_normalize_for_match_is_idempotent() -> None:
    once = normalize_for_match("National Coverage Determinations (<abbr>NCD</abbr>)")
    assert normalize_for_match(once) == once


def test_normalized_contains_rejects_an_empty_needle() -> None:
    """An empty quote must never pass as present, or every row passes."""
    assert normalized_contains("anything at all", "") is False
    assert normalized_contains("anything at all", None) is False


# --------------------------------------------------------------------------
# 4. The fetch record contract
# --------------------------------------------------------------------------


def test_fetch_record_always_carries_blocked_fields() -> None:
    from policy_eval.webtools import fetch

    rec = fetch("file:///etc/passwd")
    assert rec["blocked"] is False
    assert rec["blocked_reason"] is None
    assert rec["error"].startswith("blocked by harness")


def test_fetch_sends_the_full_browser_header_set() -> None:
    from policy_eval.webtools import BROWSER_HEADERS

    for h in (
        "User-Agent",
        "Accept",
        "Accept-Language",
        "Accept-Encoding",
        "Upgrade-Insecure-Requests",
        "Sec-Fetch-Dest",
        "Sec-Fetch-Mode",
        "Sec-Fetch-Site",
        "Sec-Fetch-User",
    ):
        assert h in BROWSER_HEADERS, h


def _main() -> int:
    tests = [
        (name, obj)
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
        except AssertionError as exc:
            failed += 1
            print(f"  FAIL  {name}: {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  ERROR {name}: {exc!r}")
        else:
            print(f"  PASS  {name}")
    print("-" * 70)
    if failed:
        print(f"FETCH-GUARD TESTS FAILED ({len(tests) - failed} / {len(tests)})")
        return 1
    print(f"FETCH-GUARD TESTS PASSED ({len(tests)} / {len(tests)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
