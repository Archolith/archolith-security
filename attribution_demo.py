#!/usr/bin/env python3
"""Attribution demo — "figure out what's from where", on the real corpus (OFFLINE).

Two things, both lightweight:
  1. The provenance MANIFEST for a full context window — and its actual byte size, to
     show it is KB (pointers + fingerprints), not a copy of the window.
  2. ATTRIBUTION: given an agent output, which context items it drew from, each with its
     trust tier — so "the output copied from an UNTRUSTED file" is visible, not hidden.

No model, no stored window. Reproduce:
  export ARCHOLITH_CORPUS=.../forked/bulletproof-react/apps/react-vite/src
  python attribution_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sec_paths  # noqa: E402,F401

from core.manifest import attribute, manifest, manifest_bytes  # noqa: E402
from adapters.archolith import from_session_briefing  # noqa: E402
from sec_corpus import build_poisoned_briefing  # noqa: E402


def main() -> int:
    briefing, _ = build_poisoned_briefing("content", 0)  # clean bpr window
    if not briefing.files:
        print("(empty briefing — set ARCHOLITH_CORPUS to the bpr react-vite src)")
        return 2
    items = from_session_briefing(briefing)

    # 1. Manifest cost for the whole window.
    content_chars = sum(len(it.content) for it in items)
    mbytes = manifest_bytes(items)
    print(f"context window: {len(items)} items, {content_chars:,} chars of content")
    print(f"provenance manifest: {mbytes:,} bytes "
          f"({mbytes / max(1, content_chars):.1%} of the content size) — pointers + "
          f"fingerprints, content NOT copied\n")
    print("manifest sample (first 3 items):")
    for rec in manifest(items)[:3]:
        print(f"  {rec}")

    # 2. Attribution: build a synthetic output that reuses lines from two real sources,
    #    then trace it back. (Stands in for a real generated feature.)
    donors = [it for it in items if it.source_type == "repo_file"][:2]
    borrowed = "\n".join(ln for d in donors
                         for ln in d.content.splitlines()[:4] if len(ln.strip()) > 20)
    output = ("// new notifications feature\n" + borrowed +
              "\nexport const useNotifications = () => null;")

    print("\nattribution of a generated output:")
    rows = attribute(output, items)
    if not rows:
        print("  (no overlap detected)")
    for a in rows[:6]:
        print(f"  <- {a.ref:<46} [{a.tier:<24}] {a.shared} lines ({a.share:.0%})")
    untrusted_hits = [a for a in rows if a.tier == "untrusted_retrieved_code"]
    print(f"\n  {len(untrusted_hits)} of {len(rows)} contributing sources are UNTRUSTED "
          f"retrieved code — visible, not hidden. (Same signal flags contamination: an "
          f"output\n  drawing heavily from an untrusted source is exactly what a security "
          f"reviewer wants surfaced.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
