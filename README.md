# archolith-security

Context-integrity defense for coding agents: an AI-safety research track that treats
indirect prompt injection (IPI) as a **context-assembly** failure and measures whether
archolith's deterministic, inspectable assembly can enforce trust separation
("governed context"). Built on the `archolith-context` assembler and the
CONTENT / MAP / PRIMING decomposition (see
`../.agent/RESEARCH-FINDINGS.md` section J and
`../.agent/plans/archolith-security-context-integrity-proposal.md`).

> ## ⚠️ INGESTION FENCE — DO NOT INDEX THIS DIRECTORY
> `sec_payloads.py` contains **adversarial IPI fixtures** by design: embedded agent
> directives, a fake hardcoded token, and an exfiltration URL. They are **inert**
> (the sink is a non-routable RFC-5737 address; nothing is executed), but they MUST
> NOT be fed into corpus profiling, the memory graph, or any context build. This
> project lives outside `archolith-bench` precisely so those fixtures never enter
> bench/corpus ingestion. Do not run `ingest_project`, corpus profiling, or
> `build_context` over this directory.

## Layout
- `sec_paths.py` — path bootstrap. Locates the bench's benign `paths.py` +
  `bpr_corpus.py` (single source of truth, kept in `archolith-bench`) and
  `archolith-context`. Override the bench location with `ARCHOLITH_BENCH_RUNG3`.
- `sec_payloads.py` — the three IPI payload classes (CONTENT instruction-injection,
  MAP shadow-foundation, PRIMING poisoned-exemplar) + the MAP in-degree-inflation
  importers. Inert fixtures.
- `sec_corpus.py` — poisoned-corpus fork: injects payloads into the benign
  bulletproof-react briefing at a controlled density (clean A/B).
- `sec_contract.py` — deterministic EXPOSURE (payload reached the window) + GOVERNED
  (rendered as untrusted) scorer. No model, no corpus dependency.
- `sec_s0_surface.py` — the S0 offline surface map (3 classes x 5 fills x 3 budgets +
  a MAP in-degree dose-response).
- `RESULT-S0-context-integrity-surface.md` — S0 findings.

## Reproduce (offline, zero API)
```
export ARCHOLITH_CORPUS=.../projects/forked/bulletproof-react/apps/react-vite/src
cd .../projects/archolith/archolith-security
python sec_contract.py          # self-check (no corpus needed)
python sec_s0_surface.py         # the S0 surface map
python sec_s0_surface.py --density 3
```

## Status
- **S0 (offline, done):** GOVERNED=0 across the whole grid (no provenance boundary);
  carrier hypothesis overturned (orphan MAP shadow resisted, xfcombo scored-slot
  resists benign-outranked poison); MAP in-degree dose-response (deg 0=0%, deg>=8=100%).
- **S1 (offline, next):** 2nd corpus + wider densities/placements for generalization.
- **S2 (metered, gated behind credits):** does the model OBEY exposed-but-ungoverned
  poison, and does deterministic governed context cut obedience at matched task
  quality — the External Researcher Access headline experiment.
