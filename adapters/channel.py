"""Channel interest classification — derive `Interest` from real capture signals.

The proxy can't read intent, but it knows the CHANNEL each item arrived on: a search
API's ad slot, a known ad-network domain, a vendor's own domain, the user's workspace.
`classify_interest` maps those signals to an `Interest` so disclosure/pumping work
without hand-tagging. An explicit per-record `interest` always wins (the caller knows
best); otherwise the channel decides; default is `organic`.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.context_item import Interest  # noqa: E402

# Substrings in a URL/ref that mark paid placement (a real deploy extends these).
_AD_MARKERS = ("doubleclick.", "googlesyndication.", "adservice.", "/sponsored",
               "utm_medium=cpc", "utm_medium=paid", "&ad=", "?ad=")
# Per-record flags a channel may carry (e.g. a search API's ad-slot marker).
_SPONSORED_FLAG_KEYS = ("sponsored", "is_ad", "is_sponsored", "ad_slot")
# Source types that are first-party by construction.
_FIRST_PARTY_TYPES = ("repo_file", "user_message", "workspace")


def _host(ref: str) -> str:
    try:
        return (urlparse(ref).hostname or "").lower()
    except Exception:
        return ""


def _truthy(v: object) -> bool:
    return v is True or (isinstance(v, str)
                         and v.strip().lower() in ("1", "true", "yes", "ad", "sponsored"))


def classify_interest(record: Mapping[str, object], *,
                      vendor_domains: frozenset[str] = frozenset()) -> Interest:
    """Map a captured record to an Interest from channel signals (explicit wins)."""
    raw = record.get("interest")
    if raw:
        try:
            return Interest(str(raw))
        except ValueError:
            pass
    if any(_truthy(record.get(k)) for k in _SPONSORED_FLAG_KEYS):
        return Interest.SPONSORED
    ref = str(record.get("source_ref", ""))
    stype = str(record.get("source_type", ""))
    host = _host(ref)
    if host and any(host == d or host.endswith("." + d) for d in vendor_domains):
        return Interest.VENDOR
    if any(m in ref.lower() for m in _AD_MARKERS):
        return Interest.SPONSORED
    if stype in _FIRST_PARTY_TYPES:
        return Interest.FIRST_PARTY
    return Interest.ORGANIC


if __name__ == "__main__":
    vendors = frozenset({"acmecorp.com"})
    cases = [
        ({"source_ref": "https://ads.doubleclick.net/x", "source_type": "web"}, "sponsored"),
        ({"source_ref": "https://search.example/r?utm_medium=cpc", "source_type": "web"}, "sponsored"),
        ({"source_ref": "https://docs.acmecorp.com/client", "source_type": "web"}, "vendor"),
        ({"source_ref": "https://developer.mozilla.org/x", "source_type": "web"}, "organic"),
        ({"source_ref": "src/app.ts", "source_type": "repo_file"}, "first_party"),
        ({"source_ref": "result:7", "source_type": "web", "sponsored": True}, "sponsored"),
        ({"source_ref": "x", "source_type": "web", "interest": "vendor"}, "vendor"),  # explicit wins
    ]
    for rec, expect in cases:
        got = classify_interest(rec, vendor_domains=vendors).value
        flag = "OK " if got == expect else "XX "
        print(f"  {flag}{rec.get('source_ref'):<42} -> {got} (expect {expect})")
        assert got == expect, (rec, got, expect)
    print("\nOK")
