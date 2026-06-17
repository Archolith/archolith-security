#!/usr/bin/env python3
"""End-to-end proof: the portable core reproduces the S0 baseline AND the defense,
using the real corpus, WITHOUT archolith's assembler.

Pipeline: bpr SessionBriefing --(adapter #1, read-only)--> [ContextItem] + an injected
untrusted payload --> govern(OFF|ANNOTATE) --> the existing S0/S1 marker contract
(`sec_contract.score_exposure`).

Expected:
  OFF      -> EXPOSED, GOVERNED=0   (faithful S0 baseline: equal-trust, no boundary)
  ANNOTATE -> EXPOSED, GOVERNED=1   (payload still in window per the Contextual-
                                     Integrity limit, but fenced + authorization-bound)

This is the framing in one runnable file: the security surface is `core` + an adapter;
the assembler is not in the loop.
Reproduce:
  export ARCHOLITH_CORPUS=.../forked/bulletproof-react/apps/react-vite/src
  python govern_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sec_paths  # noqa: E402,F401

from core import ContextItem, GovernMode, IntendedUse, TrustTier, check, govern  # noqa: E402
from adapters.archolith import from_session_briefing  # noqa: E402
from sec_contract import score_exposure  # noqa: E402
from sec_payloads import make_payloads  # noqa: E402

sys.path.insert(0, str(_BPR := Path(__file__).resolve().parent.parent
                       / "archolith-bench" / "experiments" / "context-quality"
                       / "rung3" / "corpus2-bpr"))
from bpr_corpus import build_briefing  # noqa: E402


def main() -> int:
    briefing = build_briefing()
    if not briefing.files:
        print("(empty briefing — set ARCHOLITH_CORPUS to the bpr react-vite src)")
        return 2

    # Adapter #1: briefing -> portable items (no assembler involved).
    items = from_session_briefing(briefing)

    # Inject one CONTENT payload as an untrusted retrieved item.
    payload = make_payloads("content", 1)[0]
    pay_item = ContextItem(
        content=payload.to_file().sections[0][2], source_type="repo_file",
        source_ref=payload.path, trust_tier=TrustTier.UNTRUSTED_RETRIEVED_CODE)
    items.append(pay_item)

    print(f"pipeline: briefing -> {len(items)} items "
          f"({sum(i.is_untrusted for i in items)} untrusted) + 1 injected payload\n")

    for mode in (GovernMode.OFF, GovernMode.ANNOTATE, GovernMode.ENFORCE):
        res = govern(items, mode)
        score = score_exposure(res.text, [payload])
        print(f"{mode.value:<9} exposed={score.n_exposed} "
              f"governed={score.n_governed} (gap={res.governance_gap}, "
              f"fenced={res.n_fenced}/{res.n_untrusted})")

    # Authorization binding: the injected payload may not act, regardless of exposure.
    print("\nauthorization binding on the injected payload:")
    for use in (IntendedUse.INSTRUCT_MODEL, IntendedUse.AUTHORIZE_TOOL,
                IntendedUse.PERSIST_AS_INSTRUCTION):
        d = check(pay_item, use)
        print(f"  {use.value:<24} allowed={d.allowed}")

    # Assert the framing holds.
    off = govern(items, GovernMode.OFF)
    ann = govern(items, GovernMode.ANNOTATE)
    s_off = score_exposure(off.text, [payload])
    s_ann = score_exposure(ann.text, [payload])
    assert s_off.n_exposed == 1 and s_off.n_governed == 0, "OFF must be the bare baseline"
    assert s_ann.n_exposed == 1 and s_ann.n_governed == 1, "ANNOTATE must govern the payload"
    assert not check(pay_item, IntendedUse.INSTRUCT_MODEL).allowed
    print("\nOK — baseline reproduced (GOVERNED=0) and defense governs (GOVERNED=1), "
          "no assembler in the loop.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
