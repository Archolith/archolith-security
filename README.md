# archolith-security

**Provenance-bound context governance for AI coding agents.** An AI-safety research
track on the 2026 agentic-security frontier: *bind what an agent is allowed to do to
where its context came from* — provenance and authorization as two linked graphs, so
untrusted retrieved content cannot silently become instruction, tool authorization,
memory, or published evidence. Indirect prompt injection (IPI) is the entry attack;
the defense is deterministic, inspectable, trust-tiered assembly ("governed context").
Built on the `archolith-context` assembler and the CONTENT / MAP / PRIMING decomposition.

### Canonical docs (read in this order)
- **`ROADMAP-provenance-context-validation.md`** — the strategic roadmap (workstreams:
  provenance labels, context-validation policy, governed assembly, memory-write
  provenance, retrieval-poisoning tests, tool-call justification, signed artifacts).
- **`PLAN-context-surface-levers.md`** — the engineering map of where the governance
  hooks land in `archolith-context` (governed rendering mode, `TrustTier`,
  `ContextProvenance` with `may_instruct` / `may_authorize_tools`, trace audit sink).
- **`RESULT-S0-*` / `RESULT-S1-*`** — the offline baseline: `GOVERNED=0` everywhere +
  the MAP in-degree attack (see Status).
- Workspace-internal funding/experiment proposal:
  `../.agent/plans/archolith-security-context-integrity-proposal.md`; findings digest
  in `../.agent/RESEARCH-FINDINGS.md` section J.

> ## ⚠️ INGESTION FENCE — DO NOT INDEX THIS DIRECTORY
> `sec_payloads.py` contains **adversarial IPI fixtures** by design: embedded agent
> directives, a fake hardcoded token, and an exfiltration URL. They are **inert**
> (the sink is a non-routable RFC-5737 address; nothing is executed), but they MUST
> NOT be fed into corpus profiling, the memory graph, or any context build. This
> project lives outside `archolith-bench` precisely so those fixtures never enter
> bench/corpus ingestion. Do not run `ingest_project`, corpus profiling, or
> `build_context` over this directory.

## Architecture — portable core + two adapters
The security surface is `core/`, which owns one tiny, assembler-independent context
contract. Producers (`adapters/`) convert their native context into it. **The
assembler is reference adapter #1, not a dependency** — it can be broken and the
security layer still ships. The only requirements: context arrives as *sourced items*
and there is *one enforceable chokepoint*.

- `core/context_item.py` — `ContextItem` + `TrustTier` + `Caps` (capability flags
  `instruct` / `authorize_tools` / `persist_memory` / `publish_evidence`, defaulted per
  tier via `CAP_TABLE`). Dependency-free. `derive_item` propagates lowest-trust.
- `core/policy.py` — the ACT-stage gate: `check(item, IntendedUse) -> Decision`
  (instruct / authorize-tool / persist-as-instruction / persist-as-evidence / publish).
  Authorization binding: untrusted-tier content may be evidence, nothing else.
- `core/govern.py` — the EMIT-stage renderer: `govern(items, mode)` where `OFF` is the
  faithful equal-trust baseline (`GOVERNED=0`) and `ANNOTATE`/`ENFORCE` fence untrusted
  content (`GOVERNED=1`). Fence markers match `sec_contract`'s detector.
- `adapters/archolith.py` — **#1 (read-only):** `SessionBriefing -> [ContextItem]`.
  Reads briefing TYPES only; never calls the assembler.
- `adapters/proxy.py` — **#2 (proxy-only):** an inline proxy/gateway boundary ->
  `[ContextItem]` (`from_sources` / `from_messages`). Depends on nothing in archolith.
- `govern_demo.py` — end-to-end proof on the real corpus: baseline (`GOVERNED=0`) and
  defense (`GOVERNED=1`) with no assembler in the loop.

### Offline benchmark harness (the S0/S1 measurement layer)
- `sec_paths.py` — path bootstrap to the bench's benign `paths.py` + `bpr_corpus.py`
  (single source of truth in `archolith-bench`). Override with `ARCHOLITH_BENCH_RUNG3`.
- `sec_payloads.py` — the three IPI payload classes + MAP in-degree-inflation importers.
  Inert fixtures.
- `sec_corpus.py` — poisoned-corpus fork (controlled-density A/B).
- `sec_contract.py` — deterministic EXPOSURE + GOVERNED scorer. No model.
- `sec_s0_surface.py` / `sec_s1_generalization.py` — the offline surface maps.
- `RESULT-S0-*` / `RESULT-S1-*` — S0/S1 findings.

## Reproduce (offline, zero API)
```
export ARCHOLITH_CORPUS=.../projects/forked/bulletproof-react/apps/react-vite/src
cd .../projects/archolith/archolith-security
python sec_contract.py            # self-check (no corpus needed)
python sec_s0_surface.py          # S0 surface map
python sec_s1_generalization.py   # S1 placement/density/in-degree generalization
```

## Status
- **S0 + S1 (offline, done):** `GOVERNED=0` across the entire grid (3,465 markers, 0
  governed) — no provenance boundary exists today. Placement asymmetry: CONTENT/PRIMING
  are placement-dependent; **MAP in-degree inflation is the only placement-independent
  attack** (structure beats position) and the priority target. The harness's `GOVERNED`
  metric is the pre-governance baseline.
- **Defense build (next, in `archolith-context`):** governed rendering mode +
  `TrustTier` / `ContextProvenance` (`may_instruct` / `may_authorize_tools`), flag-gated
  and default-off — see `PLAN-context-surface-levers.md`. Drives `GOVERNED` off zero.
- **S2 (metered, gated behind credits) — authorization binding, not just obedience:**
  does provenance-bound governance prevent untrusted-tier content from *causing a
  privileged action* (instruction / tool authorization / instruction-memory write) at
  matched task quality? This sidesteps the Contextual-Integrity impossibility limit on
  pure instruction/data separation, and is the External Researcher Access headline.
