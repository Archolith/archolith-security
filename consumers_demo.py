#!/usr/bin/env python3
"""Provenance consumers demo — staleness, lineage, grounding on the real corpus.

Three more readers of the same provenance graph (after attribution), all offline,
all on data already captured on each ContextItem. Reproduce:
  export ARCHOLITH_CORPUS=.../forked/bulletproof-react/apps/react-vite/src
  python consumers_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sec_paths  # noqa: E402,F401

from core import (  # noqa: E402
    GroundedLine, check_staleness, derive_item, ground, grounding_summary,
    lineage, stale_refs,
)
from core.staleness import sha256  # noqa: E402
from adapters.archolith import from_session_briefing  # noqa: E402
from sec_corpus import build_poisoned_briefing  # noqa: E402


def main() -> int:
    briefing, _ = build_poisoned_briefing("content", 0)
    if not briefing.files:
        print("(empty briefing — set ARCHOLITH_CORPUS to the bpr react-vite src)")
        return 2
    items = from_session_briefing(briefing)
    files = [it for it in items if it.source_type == "repo_file"]

    # --- 1. STALENESS: re-fingerprint the live source; flag drift -----------------
    print("== STALENESS (has captured context drifted from its source?) ==")
    # Live = the captured content for all but one item, which we 'edit' upstream.
    edited = files[0].source_ref
    live = {it.source_ref: it.content for it in items}
    live[edited] = live[edited] + "\n// upstream edit since capture"
    res = check_staleness(items, lambda it: live.get(it.source_ref))
    counts: dict[str, int] = {}
    for s in res:
        counts[s.status] = counts.get(s.status, 0) + 1
    print(f"  {counts}  -> stale/missing: {stale_refs(res)}")
    print(f"  (only {edited} changed upstream; the rest verified fresh by hash)\n")

    # --- 2. LINEAGE: a stored fact's pedigree + what it may do --------------------
    print("== LINEAGE (a derived fact's pedigree + permissions) ==")
    goal = next(it for it in items if it.trust_tier.value == "trusted_user_goal")
    untrusted = files[0]
    fact_code = derive_item(untrusted, "the app fetches through api-client", "fact:code")
    fact_goal = derive_item(goal, "user wants a notifications list", "fact:goal")
    index = {it.source_ref: it for it in (*items, fact_code, fact_goal)}
    for f in (fact_code, fact_goal):
        lg = lineage(f, index)
        print(f"  {lg.ref:<12} <- {lg.chain[1:]}  tier={lg.effective_tier} "
              f"instruct={lg.may_instruct} persist={lg.may_persist_to_memory}")
    print("  -> a fact derived from untrusted code may NOT instruct and may NOT be "
          "stored as memory (deferred-poisoning blocked at the write boundary)\n")

    # --- 3. GROUNDING: cite each output line; flag ungrounded --------------------
    print("== GROUNDING (which output lines are backed by a source?) ==")
    donor = files[0]
    output = ("// notifications feature\n"
              + "\n".join(donor.content.splitlines()[:5])
              + "\nexport const totallyInvented = () => 'no source for this line at all';")
    rows = ground(output, items)
    for g in rows[:6]:
        tag = f"{g.ref} [{g.tier}]" if g.ref else "UNGROUNDED (agent's own / unverifiable)"
        print(f"  {tag}")
    print(f"  summary: {grounding_summary(rows)}")
    print("  -> ungrounded lines are the agent's own words (synthesis or hallucination); "
          "lines grounded only in untrusted code are flagged for review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
