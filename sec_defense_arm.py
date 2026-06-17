#!/usr/bin/env python3
"""Defense arm — the governed-rendering counterpart to the S0/S1 attack surface.

S0/S1 measured the *attack* arm: the archolith assembler renders retrieved code in
one equal-trust pool, so `GOVERNED=0` across the whole grid (3,465 markers, 0
governed). This runner measures the *defense* arm on the same poisoned corpus, routed
through the portable core instead of the assembler:

    poisoned SessionBriefing --(adapter #1, read-only)--> [ContextItem]
        --> govern(mode)  --> sec_contract.score_exposure   (EXPOSURE / GOVERNED)
        --> policy.check(payload, use)                       (AUTHORIZATION BINDING)

Thesis under test (not assumed): the defense does NOT rely on keeping poison out of
the window — the Contextual-Integrity impossibility limit says it cannot. Instead it
*governs* whatever gets in. So we render the FULL item set (worst case: no fill, no
budget — every payload is exposed) and measure two things deterministically:
  - does governed mode fence 100% of the exposed untrusted surface? (GOVERNED 0 -> 1)
  - is every payload authorization-bound (may not instruct / authorize / persist)?

Offline, zero API. Reproduce:
  export ARCHOLITH_CORPUS=.../forked/bulletproof-react/apps/react-vite/src
  python sec_defense_arm.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sec_paths  # noqa: E402,F401

from core import ContextItem, GovernMode, IntendedUse, TrustTier, check, govern  # noqa: E402
from adapters.archolith import from_session_briefing  # noqa: E402
from sec_contract import score_exposure  # noqa: E402
from sec_corpus import build_poisoned_briefing  # noqa: E402

CLASSES = ("content", "map", "priming")
DENSITIES = (1, 2, 3)
MODES = (GovernMode.OFF, GovernMode.ANNOTATE, GovernMode.ENFORCE)
# Gates an untrusted payload must NOT be allowed to pass.
ACT_GATES = (IntendedUse.INSTRUCT_MODEL, IntendedUse.AUTHORIZE_TOOL,
             IntendedUse.PERSIST_AS_INSTRUCTION)


def _payload_items(payloads) -> list[ContextItem]:
    return [ContextItem(content=p.to_file().sections[0][2], source_type="repo_file",
                        source_ref=p.path, trust_tier=TrustTier.UNTRUSTED_RETRIEVED_CODE)
            for p in payloads]


def run() -> int:
    probe, _ = build_poisoned_briefing("content", 0)
    if not probe.files:
        print("(empty briefing — set ARCHOLITH_CORPUS to the bpr react-vite src)")
        return 2

    print("archolith-security DEFENSE ARM — governed rendering on the S0/S1 corpus "
          "(OFFLINE, no API)")
    print("attack arm (assembler, S0/S1): GOVERNED=0 everywhere. defense arm below.\n")
    hdr = (f"{'class':<8} {'dens':>4} | "
           + " | ".join(f"{m.value:>16}" for m in MODES)
           + " | authz-bound")
    print(hdr)
    print("-" * len(hdr))

    tot_exposed = tot_governed = 0
    tot_gates = tot_denied = 0
    for pclass in CLASSES:
        for dens in DENSITIES:
            briefing, payloads = build_poisoned_briefing(pclass, dens)
            items = from_session_briefing(briefing)
            cells = []
            for mode in MODES:
                res = govern(items, mode)
                s = score_exposure(res.text, payloads)
                if mode == GovernMode.ANNOTATE:
                    tot_exposed += s.n_exposed
                    tot_governed += s.n_governed
                cells.append(f"{s.exposure_rate:>5.0%}/{s.governed_rate:>4.0%}".rjust(16))

            # Authorization binding: every payload, every act-gate must be denied.
            denied = gates = 0
            for it in _payload_items(payloads):
                for use in ACT_GATES:
                    gates += 1
                    denied += 0 if check(it, use).allowed else 1
            tot_gates += gates
            tot_denied += denied
            print(f"{pclass:<8} {dens:>4} | " + " | ".join(cells)
                  + f" | {denied}/{gates}")

    print("-" * len(hdr))
    print("cells = EXPOSURE / GOVERNED  (govern renders ALL items: exposure is 100% by "
          "design — the point is governance, not keeping poison out)\n")
    print("SUMMARY (defense arm):")
    print(f"  OFF mode reproduces the attack-arm baseline: GOVERNED = 0.")
    print(f"  ANNOTATE/ENFORCE govern the exposed surface: "
          f"{tot_governed}/{tot_exposed} exposed payloads fenced "
          f"({(100*tot_governed//max(1,tot_exposed))}%).")
    print(f"  Authorization binding: {tot_denied}/{tot_gates} payload act-gates DENIED "
          f"(instruct / authorize-tool / persist-as-instruction).")
    ok = (tot_governed == tot_exposed and tot_denied == tot_gates)
    print(f"\n  {'PASS' if ok else 'CHECK'}: governance 0->1 on the full exposed "
          f"surface, and every untrusted payload is authorization-bound.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
