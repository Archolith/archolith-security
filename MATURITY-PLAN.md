# archolith-security — Maturity assessment & plan

Status: planning (2026-06-17). Verdict: **research prototype, NOT fileable yet.** This
maps what's solid, what blocks maturity, and the order to close the gaps.

## Honest maturity verdict
Strong *substrate and offline rigor*; weak *external validity, integration, and framing*.
Concretely, it is not fileable because:
1. **No threat model.** A security project must state its adversary, trust assumptions,
   in/out of scope, and explicit non-goals. We've discovered these piecemeal (authority
   vs influence; channel-marked only; can't police the host) but never consolidated.
2. **Evaluation is homemade.** S2 used hand-written payloads on one model (DeepSeek) /
   one corpus (bpr), scored by string match. There is a standard benchmark for exactly
   this — **AgentDojo** (70 tools, 97 tasks, 27 injection targets) — and competing
   defenses (**PromptArmor**, **AgentArmor**) report numbers on it. We report none.
3. **Not situated against prior art.** No positioning vs CaMeL (capability/provenance-
   based design), spotlighting/sandwiching, tool-result parsing, OWASP Agentic Top 10.
4. **No real integration.** The adapters are stubs; nothing intercepts a live agent.
   Governed rendering exists in `core` but is NOT wired into `archolith-context`.
5. **Thin tests.** One pytest file (capture integrity); everything else is `__main__`
   self-tests. No coverage, no CI.

## What IS solid (don't rebuild)
- The provenance substrate: one `ContextItem` graph, 7 consumers across two integrity
  axes (authority: govern/policy; influence: disclosure/pumping; + attribution/
  staleness/lineage/grounding), all offline/model-independent, KB-scale.
- Offline rigor + honest calibration: GOVERNED=0 baseline, the conservative trust model
  proven by tier-spoofing (hardened + regression-tested), and the *condition-specific*
  S2 result reported without overclaiming.
- The conceptual frame: authorization binding for authority, disclosure for influence.

## Gap bucket A — unbuilt roadmap workstreams (plans we adopted but didn't run)
From `ROADMAP-provenance-context-validation.md`:
- ~~**#6 Tool-call provenance validation**~~ **DONE (`31ec9d5`, `core/toolcall.py`).** Blocks
  tainted untrusted-origin data / secret material flowing to an exfiltration sink (the
  lethal trifecta) on a data-flow criterion, + tool calls authorized only by untrusted
  content. 9 tests + `lethal_trifecta_demo.py`. See `RESULT-security-core.md`.
- ~~**#4 Memory write firewall**~~ **DONE (`31ec9d5`, `core/memory_firewall.py`).** Gates
  persistence by inherited caps — instruction-grade requires `may_instruct`, so an
  untrusted-derived fact can never become instruction memory (deferred poisoning blocked
  at the write).
- **#3 Governed rendering in `archolith-context` — NOT WIRED.** Built in `core`, never
  integrated into the live assembler (we decoupled on purpose; integration is still owed).
- **#7 Generated-artifact provenance — PARKED** (PR #2: signing/fingerprinting outputs).

## Gap bucket B — cross-cutting credibility (mostly cheap, mostly offline)
- **Threat-model & scope document** (highest credibility-per-effort; offline).
- **Prior-art positioning** (CaMeL, AgentArmor, PromptArmor, spotlighting, tool-result
  parsing, OWASP, C2PA) (offline).
- **Standard-benchmark evaluation on AgentDojo** (metered; turns homemade into comparable).
- **Real pytest suite + CI** across all modules (offline).
- **Reference integration** — an actual proxy / MCP interceptor (the product path).

## Unexplored directions (beyond the adopted roadmap)
- **The other half of "two linked graphs":** we built provenance + a static policy table,
  not the *authorization graph* (which tools/actions, and how authority propagates).
- **Multi-agent provenance propagation** — when agent A hands context to agent B, trust/
  provenance must carry; 2026 work flags this authorization-propagation problem.
- **Data-flow / exfiltration framing** — define attack success as actual leakage of
  tainted data to a sink (matches the credible threat models), not "model said X".

## Proposed sequence (credibility per effort)
- ~~**Tier A — frame & harden**~~ **DONE (`8b88121`):** (1) `THREAT-MODEL.md`; (2)
  `PRIOR-ART.md` (vs CaMeL/PromptArmor/AgentArmor/AgentDojo/...); (3) real pytest suite
  (46 tests, stdlib-only core runs anywhere; archolith-adapter test importorskips) +
  GitHub Actions CI. The existing work is now legible and trustworthy.
- ~~**Tier B — build the security core**~~ **DONE (`31ec9d5`):** tool-call provenance
  enforcement (#6) with the data-flow/exfiltration criterion + memory write firewall (#4).
  The substantive maturity jump — enforcement, not just labeling.
- **Tier C — external validity (metered):** (6) port the S2 obedience/leakage eval onto
  **AgentDojo** so results are comparable to PromptArmor/AgentArmor.
- **Tier D — productize:** (7) a reference proxy/MCP interceptor; (8) wire governed
  rendering into `archolith-context`.

**Status (2026-06-17): Tier A + Tier B DONE.** Remaining before a credible filing:
**Tier C (a first AgentDojo number)** — the external-validity step — and the productization
in Tier D. The framing and the security core are in place; what's missing is a
standard-benchmark result to report next to CaMeL/PromptArmor/AgentArmor.

## Sources (prior art / benchmarks to engage)
- AgentDojo (benchmark): arxiv 2406.13352
- PromptArmor (ICLR 2026 defense): arxiv 2507.15219
- AgentArmor (runtime-trace program analysis): arxiv 2508.01249
- Tool-result-parsing IPI defense: arxiv 2601.04795
- Data-flow threat model (leakage-as-success): see 2026 IPI exfiltration studies
