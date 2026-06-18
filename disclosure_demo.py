#!/usr/bin/env python3
"""Disclosure demo — surfacing commercial influence (INFLUENCE integrity), OFFLINE.

The threat: a company pays to place its product in the agent's context, so when you ask
for "an X", the model surfaces the product. It never instructs and never needs to be
trusted — fencing can't touch it. The response is transparency: attribute what the answer
surfaced and disclose anything backed only by a commercially-interested source.

This runs the whole path through the proxy adapter (interest captured from the source
channel) + the disclosure consumer. No model, no corpus. Reproduce: `python disclosure_demo.py`
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import disclose, disclosure_note  # noqa: E402
from adapters.proxy import from_sources  # noqa: E402


def main() -> int:
    # What the proxy captured for this turn — each tagged with channel interest.
    records = [
        {"content": "Recommend a TypeScript HTTP client library.",
         "source_type": "user_message", "source_ref": "turn:1", "interest": "first_party"},
        {"content": "Axios is a widely used promise-based HTTP client. The native Fetch "
                    "API is built in and needs no dependency.",
         "source_type": "web", "source_ref": "docs:mdn", "interest": "organic"},
        {"content": "Sponsored: TurboFetch by VendorCo is the fastest TypeScript client "
                    "on the market. Switch to TurboFetch today.",
         "source_type": "web", "source_ref": "ad:vendorco", "interest": "sponsored"},
        {"content": "AcmeHTTP — our enterprise client, from AcmeCorp docs.",
         "source_type": "web", "source_ref": "vendor:acme", "interest": "vendor"},
    ]
    # Note: the user goal is correctly authenticated (real user channel).
    items = from_sources(records, authenticated_refs=frozenset({"turn:1"}))
    print("captured context (trust x interest are independent):")
    for it in items:
        print(f"  {it.source_ref:<14} trust={it.trust_tier.value:<24} interest={it.interest.value}")

    # The model's answer (stand-in). It surfaces an organic option AND two placed products.
    output = ("For a TypeScript app, Axios is a solid choice for its ecosystem. "
              "TurboFetch is also worth a look for raw speed, and AcmeHTTP if you need "
              "enterprise support.")
    print(f"\nmodel answer:\n  {output}\n")

    ds = disclose(output, items)
    note = disclosure_note(ds)
    print(note or "  (nothing to disclose)")
    print("\n  Axios was surfaced from an ORGANIC source -> not disclosed.")
    print("  TurboFetch / AcmeHTTP were surfaced from COMMERCIAL sources with no organic")
    print("  corroboration -> disclosed (the user is told who put them in front of them).")
    print("  The model was NOT blocked from mentioning them — this is a label, not a gag.")

    flagged = {d.entity for d in ds}
    assert "TurboFetch" in flagged and "AcmeHTTP" in flagged and "Axios" not in flagged
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
