# RESULT — Provenance consumers: staleness, lineage, grounding (OFFLINE)

Status: DONE (offline, zero API, model-independent). Code: `core/staleness.py`,
`core/lineage.py`, `core/grounding.py`; demo `consumers_demo.py` (+ attribution in
`core/manifest.py`). Reproduce: `python consumers_demo.py`.

## Point
The provenance graph (origin + lineage on every `ContextItem`) is a substrate; security
was its first consumer, attribution the second. These are three more — each a small,
offline reader of fields **already captured**, confirming the reframe that "what's from
where" is generally useful, not just a security gate, and that it stays lightweight.

## 1. Staleness — has captured context drifted from its source?
Re-fingerprint the live source and compare to the item's stored `content_sha256` (the
generalized map-drift freshness check). On the bpr window with one file edited upstream:
```
{'fresh': 35, 'stale': 1}  -> stale: features/comments/api/create-comment.ts
```
35 items verified fresh by hash, the changed one flagged — no content stored to do it.

## 2. Lineage — a derived fact's pedigree and permissions
`derive_item` inherits the lowest trust of a fact's sources; `lineage()` walks the
`derived_from` chain so you can check, before acting on or persisting a fact, where it
came from and what it may do:
```
fact:code  <- ['features/.../create-comment.ts']  tier=untrusted  instruct=False persist=False
fact:goal  <- ['session_goal']                    tier=trusted    instruct=False persist=True
```
**A fact derived from untrusted code may neither instruct nor be stored as memory** —
the deferred memory-poisoning attack is blocked at the *write* boundary, not discovered
later. Also plain memory hygiene: every stored fact carries its origin and trust.

## 3. Grounding — which output lines are backed by a source?
Cite each distinctive output line to the item that contains it; flag the rest:
```
UNGROUNDED (agent's own / unverifiable)
features/comments/api/create-comment.ts [untrusted_retrieved_code]   x4
summary: {'lines': 6, 'ungrounded': 2, 'untrusted_grounded': 4}
```
Outputs become citable ("per `src/...`"); ungrounded lines are the agent's own words
(synthesis or hallucination); lines grounded only in *untrusted* code are flagged for
review — observability and a security signal from the same lookup.

## Takeaway
Four consumers now run off one provenance graph — security gate, attribution, staleness,
lineage, grounding — all offline, model-independent, on already-captured data at KB
scale. Provenance is the product surface; each use is a thin reader. The data-heavy
worry does not materialize because nothing here stores content: it stores and compares
fingerprints and references.

## Next (still latent, same data)
- Wire staleness into a freshness GUARD that drops/refreshes stale items before assembly
  (closes the loop with the map-drift result).
- Persist the per-turn manifest to a JSONL audit trail (the `TraceStore` idea) for
  cross-session attribution.
- Harden the adapters against the tier-spoofing bypasses (capture integrity).
